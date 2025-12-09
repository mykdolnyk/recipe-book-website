from logging import getLogger
from flask.blueprints import Blueprint
from flask import abort, jsonify, request
from flask_login import current_user, login_required
from backend.utils.misc import ObjectManager, safe_commit
from backend.utils.errors import ErrorCode, create_error_response
from backend.utils.login import is_owner_or_superuser, superuser_only
from backend.utils.pagination import paginate
from backend.recipes.models import MealType, Recipe, RecipeTag
from backend.recipes.models import RecipePublicationApplication as RecipeApp
from backend.recipes.schemas import RecipeDetailedSchema, RecipePublicationApplicationCreate as RecipeAppCreate, RecipeUpdateStatus
from backend.recipes.schemas import RecipePublicationApplicationSchema as RecipeAppSchema
from backend.recipes.schemas import RecipePublicationApplicationUpdate as RecipeAppUpdate
from backend.recipes.schemas import MealTypeSchema, RecipeCreate, RecipeUpdate, RecipeSchema, RecipeTagCreate, RecipeTagSchema, RecipeTagUpdate
from app_factory import db
logger = getLogger(__name__)


recipes_bp = Blueprint(
    name='recipes',
    import_name=__name__,
    url_prefix='/api',
)


@recipes_bp.route('/recipes', methods=['POST'])
@login_required
def create_recipe():
    manager = ObjectManager(
        db_model=Recipe,
        create_schema=RecipeCreate,
        get_schema=RecipeSchema
    )
    manager.create_object(
        data=request.get_json()
    )

    response = manager.generate_response()
    return response


@recipes_bp.route('/recipes', methods=['GET'])
def get_recipe_list():
    pagination = paginate(
        request_args=request.args,
        sqlalchemy_query=Recipe.ua_query(),
        pydantic_model=RecipeSchema,
        list_name='recipe_list',
    )

    return jsonify(pagination)


@recipes_bp.route('/recipes/<int:id>', methods=['GET'])
def get_recipe(id: int):
    recipe = Recipe.ua_query().filter_by(id=id).first()
    if not recipe:
        abort(404)

    response = RecipeSchema.model_validate(recipe).model_dump()
    return jsonify(response)


@recipes_bp.route('/recipes/<int:id>/detailed', methods=['GET'])
@superuser_only
def get_recipe_detailed(id: int):
    recipe = Recipe.ua_query().filter_by(id=id).first()
    if not recipe:
        abort(404)

    response = RecipeDetailedSchema.model_validate(recipe).model_dump()
    return jsonify(response)


@recipes_bp.route('/recipes/<int:id>', methods=['PUT'])
def edit_recipe(id: int):
    recipe = Recipe.ua_query().filter_by(id=id).first()
    if not recipe:
        abort(404)
    if current_user.is_anonymous:
        abort(401)
    if not is_owner_or_superuser(recipe.author):
        abort(403)
    
    
    manager = ObjectManager(
        db_model=Recipe,
        update_schema=RecipeUpdate,
        get_schema=RecipeSchema,
    )
    manager.update_object(
        obj=recipe,
        data=request.get_json()
    )

    response = manager.generate_response()
    return response



@recipes_bp.route('/recipes/<int:id>', methods=['DELETE'])
def delete_recipe(id: int):
    recipe = Recipe.ua_query().filter_by(id=id).first()
    if not recipe:
        abort(404)
    if current_user.is_anonymous:
        abort(401)
    if not is_owner_or_superuser(recipe.author):
        abort(403)

    recipe.is_visible = False
    errors = safe_commit(db.session)
    if errors:
        return errors

    return '', 204


@recipes_bp.route('/recipes/<int:id>/publish', methods=['POST'])
def publish_recipe(id: int):
    recipe = Recipe.ua_query().filter_by(id=id).first()
    if not recipe:
        abort(404)

    if recipe.is_published:
        abort(400)

    application = RecipeApp.query.filter(
        RecipeApp.recipe == recipe,
        RecipeApp.status == RecipeApp.STATUSES.NOT_REVIEWED,
    ).first()
    # If not reviewed application for the recipe already exists
    if application:
        return create_error_response(ErrorCode.ALREADY_EXISTS, status_code=409)

    manager = ObjectManager(
        db_model=RecipeApp,
        create_schema=RecipeAppCreate,
        get_schema=RecipeAppSchema
    )
    manager.create_object(
        data=request.get_json(),
        commit=False
    )
    manager.object.recipe_id = id
    manager.commit_changes()
    
    response = manager.generate_response()

    return response


@recipes_bp.route('/recipes/applications', methods=['GET'])
def get_recipe_application_list():
    if current_user.is_superuser:
        query = RecipeApp.query
    elif current_user.is_anonymous:
        abort(401)
    else:
        # only the current user's applications
        query = RecipeApp.query.filter(
            RecipeApp.recipe.has(author_id=current_user.id)
        )

    pagination = paginate(
        request_args=request.args,
        sqlalchemy_query=query,
        pydantic_model=RecipeAppSchema,
        list_name='recipe_publication_application_list',
    )

    return jsonify(pagination)


@recipes_bp.route('/recipes/applications/<int:id>', methods=['GET'])
def get_recipe_application(id: int):
    if current_user.is_superuser:
        query = RecipeApp.query
    else:
        # only the current user's applications
        query = RecipeApp.query.filter(
            RecipeApp.recipe.has(author_id=current_user.id)
        )

    application = query.filter_by(id=id).first()
    if not application:
        abort(404)

    response = RecipeAppSchema.model_validate(application).model_dump()
    return jsonify(response)


@recipes_bp.route('/recipes/applications/<int:id>', methods=['PUT'])
@superuser_only
def update_recipe_application(id: int):
    application = RecipeApp.query.filter_by(id=id).first()
    if not application:
        abort(404)
        
    application_manager = ObjectManager(
        db_model=RecipeApp,
        update_schema=RecipeAppUpdate,
        get_schema=RecipeAppSchema,
    )
    application_manager.update_object(
        obj=application,
        data=request.get_json()
    )
    # Update the `last_reviewed_by` field
    application_manager.object.last_reviewed_by_id = current_user.id
    application_manager.commit_changes()
    
    if application_manager.object.status == RecipeApp.STATUSES.ACCEPTED:
        # Update the recipe's `is_published` to True
        recipe_manager = ObjectManager(
            db_model=Recipe,
            update_schema=RecipeUpdateStatus,
            get_schema=RecipeDetailedSchema,
        )
        recipe_manager.update_object(
            obj=application.recipe,
            data={"is_published": True}
        )

    response = application_manager.generate_response()
    return response


@recipes_bp.route('/recipes/<int:id>/status', methods=['PUT'])
@superuser_only
def change_recipe_status(id: int):
    recipe = Recipe.query.filter_by(id=id).first()
    if not recipe:
        abort(404)

    manager = ObjectManager(
        db_model=Recipe,
        update_schema=RecipeUpdateStatus,
        get_schema=RecipeDetailedSchema,
    )
    manager.update_object(
        obj=recipe,
        data=request.get_json()
    )

    response = manager.generate_response()
    return response


@recipes_bp.route('/recipe-tags', methods=['GET'])
def get_recipe_tag_list():
    pagination = paginate(
        request_args=request.args,
        sqlalchemy_query=RecipeTag.query,
        pydantic_model=RecipeTagSchema,
        list_name='recipe_tag_list',
    )

    return jsonify(pagination)


@recipes_bp.route('/recipe-tags/<int:id>', methods=['GET'])
def get_recipe_tag(id: int):
    tag = RecipeTag.query.filter_by(id=id).first()
    if not tag:
        abort(404)

    response = RecipeTagSchema.model_validate(tag).model_dump()
    return jsonify(response)


@recipes_bp.route('/recipe-tags', methods=['POST'])
@superuser_only
def create_recipe_tag():
    manager = ObjectManager(
        db_model=RecipeTag,
        create_schema=RecipeTagCreate,
        get_schema=RecipeTagSchema
    )
    manager.create_object(request.get_json())

    response = manager.generate_response()

    return response


@recipes_bp.route('/recipe-tags/<int:id>', methods=['PUT'])
@superuser_only
def update_recipe_tag(id: int):
    tag = RecipeTag.query.filter_by(id=id).first()
    if not tag:
        abort(404)

    manager = ObjectManager(
        db_model=RecipeTag,
        update_schema=RecipeTagUpdate,
        get_schema=RecipeTagSchema,
    )
    manager.update_object(
        obj=tag,
        data=request.get_json()
    )
    
    response = manager.generate_response()
    return response


@recipes_bp.route('/recipe-tags/<int:id>', methods=['DELETE'])
@superuser_only
def delete_recipe_tag(id: int):
    tag = RecipeTag.query.filter_by(id=id).first()
    if not tag:
        abort(404)

    db.session.delete(tag)
    errors = safe_commit(db.session)
    if errors:
        return errors

    return '', 204


@recipes_bp.route('/meal-types/', methods=['GET'])
def get_meal_type_list():
    # todo: cache aggresively
    pagination = paginate(
        request_args=request.args,
        sqlalchemy_query=MealType.query,
        pydantic_model=MealTypeSchema,
        list_name='meal_type_list',
    )

    return jsonify(pagination)


@recipes_bp.route('/meal-types/<int:id>', methods=['GET'])
def get_meal_type(id: int):
    mtype = MealType.query.filter_by(id=id).first()
    if not mtype:
        abort(404)

    response = MealTypeSchema.model_validate(mtype).model_dump()
    return jsonify(response)
