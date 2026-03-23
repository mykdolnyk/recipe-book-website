import json
from logging import getLogger
from flask.blueprints import Blueprint
from flask import abort, jsonify, request
from flask_login import current_user, login_required
from pydantic import ValidationError
from backend.recipes.helpers import create_recipe_mix, search_recipes, get_popular_recipes_query
from backend.recipes.tasks import calculate_popular_recipes
from backend.utils.misc import ObjectManager, safe_commit
from backend.utils.errors import ErrorCode, create_error_response
from backend.utils.login import is_owner_or_superuser, superuser_only
from backend.utils.pagination import paginate
from backend.recipes.models import Like, MealType, Recipe, RecipeMix, RecipeTag
from backend.recipes.models import RecipePublicationApplication as RecipeApp
from backend.recipes.schemas import RecipeDetailedSchema, RecipeMixCreate, RecipeMixSchema, RecipeMixUpdate, RecipePublicationApplicationCreate as RecipeAppCreate, RecipeUpdateStatus
from backend.recipes.schemas import RecipePublicationApplicationSchema as RecipeAppSchema
from backend.recipes.schemas import RecipePublicationApplicationUpdate as RecipeAppUpdate
from backend.recipes.schemas import MealTypeSchema, RecipeCreate, RecipeUpdate, RecipeSchema, RecipeTagCreate, RecipeTagSchema, RecipeTagUpdate
from app_factory import db
from app_factory import redis_client
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
        data=request.get_json(),
        exclude_for_db='tags'
    )

    if manager.success:
        # Add tags:
        tags = manager.schema_data.tags

        if tags:
            recipe: Recipe = manager.object

            recipe.tags = RecipeTag.query.filter(
                RecipeTag.id.in_(tags)
            ).all()

            manager.commit_changes()

    response = manager.generate_response()
    return response


@recipes_bp.route('/recipes', methods=['GET'])
def get_recipe_list():
    query = Recipe.ua_query(
        force_exclude_hidden=True,
        force_exclude_not_personal_unpublished=True)

    # Filter by author if needed
    author_id = request.args.get('author_id')
    if author_id:
        query = query.filter(Recipe.author_id == int(author_id))

    # Filter by current user's likes
    liked = request.args.get('liked')
    if liked and liked.lower() in ('true', '1'):
        query = query.filter(Recipe.likes.any(Like.user_id == current_user.id))

    # Filter by whether to include unpublished
    published_only = request.args.get('published_only')
    if published_only and published_only.lower() in ('true', '1'):
        query = query.filter(Recipe.is_published == True)

    pagination = paginate(
        request_args=request.args,
        sqlalchemy_query=query,
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
    cache_key = 'recipe-tag-list-response'
    response = redis_client.get(cache_key)
    
    if response is not None:
        response = json.loads(response)
    else:
        pagination = paginate(
            request_args=request.args,
            sqlalchemy_query=RecipeTag.query,
            pydantic_model=RecipeTagSchema,
            list_name='recipe_tag_list',
            no_per_page_limit=True
        )
        response = jsonify(pagination).get_json()
        redis_client.set(cache_key, json.dumps(response), 3600)

    return response


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

    redis_client.delete('recipe-tag-list-response')
    redis_client.delete('recipe-related-objects')

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
    
    redis_client.delete('recipe-tag-list-response')
    redis_client.delete('recipe-related-objects')

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
    
    redis_client.delete('recipe-tag-list-response')
    redis_client.delete('recipe-related-objects')

    return '', 204


@recipes_bp.route('/meal-types', methods=['GET'])
def get_meal_type_list():
    
    cache_key = 'meal-types-list-response'
    response = redis_client.get(cache_key)
    
    if response is not None:
        response = json.loads(response)
    else:
        pagination = paginate(
            request_args=request.args,
            sqlalchemy_query=MealType.query,
            pydantic_model=MealTypeSchema,
            list_name='meal_type_list',
            no_per_page_limit=True
        )
        response = jsonify(pagination).get_json()
        redis_client.set(cache_key, json.dumps(response), 3600)

    return response


@recipes_bp.route('/meal-types/<int:id>', methods=['GET'])
def get_meal_type(id: int):
    mtype = MealType.query.filter_by(id=id).first()
    if not mtype:
        abort(404)

    response = MealTypeSchema.model_validate(mtype).model_dump()
    return jsonify(response)


@recipes_bp.route('/recipe-mixes', methods=['GET'])
def get_mix_list():
    if current_user.is_superuser:
        query = RecipeMix.query
    else:
        query = RecipeMix.query.filter(RecipeMix.author_id == current_user.id)

    query = query.order_by(RecipeMix.created_on.desc())

    pagination = paginate(
        request_args=request.args,
        sqlalchemy_query=query,
        pydantic_model=RecipeMixSchema,
        list_name='recipe_mix_list',
    )

    return jsonify(pagination)


@recipes_bp.route('/recipe-mixes/<int:id>', methods=['GET'])
def get_mix(id: int):
    if current_user.is_superuser:
        query = RecipeMix.query
    else:
        query = RecipeMix.query.filter(RecipeMix.author_id == current_user.id)

    recipe_mix = query.filter_by(id=id).first()
    if not recipe_mix:
        abort(404)

    response = RecipeMixSchema.model_validate(recipe_mix).model_dump()
    return jsonify(response)


@recipes_bp.route('/recipe-mixes', methods=['POST'])
def create_mix():
    try:
        mix_settings = RecipeMixCreate(**request.get_json()).model_dump()
    except ValidationError as error:
        return create_error_response(error)

    recipe_mix = create_recipe_mix(**mix_settings,
                                   author=current_user)

    if recipe_mix is None:
        return create_error_response(ErrorCode.NO_COMPATIBLE_RECIPES, status_code=400)

    response = RecipeMixSchema.model_validate(recipe_mix).model_dump()
    return jsonify(response)


@recipes_bp.route('/recipe-mixes/<int:id>', methods=['DELETE'])
def delete_mix(id: int):
    if current_user.is_superuser:
        query = RecipeMix.query
    else:
        query = RecipeMix.query.filter(RecipeMix.author_id == current_user.id)

    mix = query.filter_by(id=id).first()
    if not mix:
        abort(404)

    db.session.delete(mix)
    errors = safe_commit(db.session)
    if errors:
        return errors

    return '', 204


@recipes_bp.route('/recipe-mixes/<int:id>', methods=['PUT'])
def update_mix(id: int):
    if current_user.is_superuser:
        query = RecipeMix.query
    else:
        query = RecipeMix.query.filter(RecipeMix.author_id == current_user.id)

    recipe_mix = query.filter_by(id=id).first()
    if not recipe_mix:
        abort(404)

    manager = ObjectManager(
        db_model=RecipeMix,
        update_schema=RecipeMixUpdate,
        get_schema=RecipeMixSchema,
    )
    manager.update_object(
        obj=recipe_mix,
        data=request.get_json()
    )

    response = manager.generate_response()
    return response


@recipes_bp.route('/recipes/search', methods=['GET'])
def recipe_search():
    request_args = request.args

    query = search_recipes(request_args=request_args)

    pagination = paginate(
        request_args=request_args,
        sqlalchemy_query=query,
        pydantic_model=RecipeSchema,
        list_name='recipe_list',
    )

    return jsonify(pagination)


@recipes_bp.route('/recipes/<int:id>/like', methods=['GET'])
def check_recipe_like(id: int):
    recipe = Recipe.ua_query().filter_by(id=id).first()
    if not recipe:
        abort(404)
    if current_user.is_anonymous:
        abort(401)

    like = Like.query.filter(Like.recipe_id == recipe.id,
                             Like.user_id == current_user.id).first()

    response = {
        "recipe_id": recipe.id,
        "user_id": current_user.id,
        "liked": True if like is not None else False
    }

    return jsonify(response)


@recipes_bp.route('/recipes/<int:id>/like', methods=['POST'])
def like_recipe(id: int):
    recipe = Recipe.ua_query().filter_by(id=id).first()
    if not recipe:
        abort(404)
    if current_user.is_anonymous:
        abort(401)

    like = Like.query.filter(Like.recipe_id == recipe.id,
                             Like.user_id == current_user.id).first()

    if like is not None:
        return '', 204

    like = Like(
        recipe_id=recipe.id,
        user_id=current_user.id
    )
    db.session.add(like)
    db.session.commit()

    return '', 201


@recipes_bp.route('/recipes/<int:id>/like', methods=['DELETE'])
def unlike_recipe(id: int):
    recipe = Recipe.ua_query().filter_by(id=id).first()
    if not recipe:
        abort(404)
    if current_user.is_anonymous:
        abort(401)

    like = Like.query.filter(Like.recipe_id == recipe.id,
                             Like.user_id == current_user.id).first()
    if like is None:
        return '', 204

    db.session.delete(like)
    db.session.commit()

    return '', 204


@recipes_bp.route('/recipes/popular', methods=['GET'])
def get_popular_recipes():
    recipe_id_list = json.loads(redis_client.get('popular_recipes'))
    
    popular_recipes = Recipe.ua_query().filter(Recipe.id.in_(recipe_id_list))
    recipe_list = [RecipeSchema.model_validate(obj).model_dump() for obj in popular_recipes]
    return jsonify(recipe_list)
