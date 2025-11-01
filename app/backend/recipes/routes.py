from logging import getLogger
from flask.blueprints import Blueprint
from flask import abort, json, jsonify, request
from flask_login import login_required
from pydantic import ValidationError
from backend.utils.misc import safe_commit
from backend.utils.errors import ErrorCode, create_error_response
from backend.recipes.helpers import create_recipe_instance
from backend.recipes.models import Recipe, RecipeTag
from backend.recipes.schemas import RecipeCreate, RecipeUpdate, RecipeSchema, RecipeTagCreate, RecipeTagSchema, RecipeTagUpdate
from app_factory import db
from backend.utils.login import is_user_or_superuser, superuser_only
logger = getLogger(__name__)


recipes_bp = Blueprint(
    name='recipes',
    import_name=__name__,
    url_prefix='/api',
)


@recipes_bp.route('/recipes', methods=['POST'])
@login_required
def create_recipe():
    try:
        recipe_schema = RecipeCreate(**request.get_json())
    except ValidationError as error:
        return jsonify({"errors": error.errors(include_url=False, include_context=False)}), 400

    try:
        recipe = create_recipe_instance(recipe_schema)
    except Exception as e:
        logger.exception(e)
        return create_error_response(ErrorCode.UNKNOWN)

    response = RecipeSchema.model_validate(recipe).model_dump()
    return jsonify(response)


@recipes_bp.route('/recipes', methods=['GET'])
def get_recipe_list():
    page = request.args.get('page', 0)
    per_page = request.args.get('per-page', 5)

    pagination = Recipe.visible().paginate(page=page,
                                           per_page=per_page,
                                           max_per_page=25,
                                           error_out=False)

    recipe_list = [RecipeSchema.model_validate(recipe).model_dump()
                   for recipe in pagination.items]

    return jsonify({
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "recipe_list": recipe_list
    })


@recipes_bp.route('/recipes/<int:id>', methods=['GET'])
def get_recipe(id: int):
    recipe = Recipe.visible().filter_by(id=id).first()
    if not recipe:
        abort(404)

    response = RecipeSchema.model_validate(recipe).model_dump()
    return jsonify(response)


@recipes_bp.route('/recipes/<int:id>', methods=['PUT'])
def edit_recipe(id: int):
    try:
        recipe_schema = RecipeUpdate(**request.get_json())
    except ValidationError as error:
        return jsonify({"errors": error.errors(include_url=False, include_context=False)}), 400

    recipe = Recipe.visible().filter_by(id=id).first()
    if not recipe:
        abort(404)
        
    if not is_user_or_superuser(recipe.author):
        abort(403)


    new_data = recipe_schema.model_dump(exclude_unset=True)
    # Update the values of the DB model
    for key, value in new_data.items():
        setattr(recipe, key, value)

    errors = safe_commit(db, logger)
    if errors:
        return errors

    response = RecipeSchema.model_validate(recipe).model_dump()

    return jsonify(response)


@recipes_bp.route('/recipes/<int:id>', methods=['DELETE'])
def delete_recipe(id: int):
    recipe = Recipe.visible().filter_by(id=id).first()
    if not recipe:
        abort(404)
        
    if not is_user_or_superuser(recipe.author):
        abort(403)

    recipe.is_visible = False
    errors = safe_commit(db, logger)
    if errors:
        return errors

    return '', 204


@recipes_bp.route('/recipe-tags', methods=['GET'])
def get_recipe_tag_list():
    page = request.args.get('page', 0)
    per_page = request.args.get('per-page', 5)

    pagination = RecipeTag.query.paginate(page=page,
                                          per_page=per_page,
                                          max_per_page=25,
                                          error_out=False)

    tag_list = [RecipeTagSchema.model_validate(tag).model_dump()
                for tag in pagination.items]

    return jsonify({
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "recipe_tag_list": tag_list
    })


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
    try:
        schema = RecipeTagCreate(**request.get_json())
    except ValidationError as error:
        return jsonify({"errors": error.errors(include_url=False, include_context=False)}), 400

    new_tag = RecipeTag(**schema.model_dump())
    
    db.session.add(new_tag)
    errors = safe_commit(db, logger)
    if errors:
        return errors
    
    response = RecipeTagSchema.model_validate(new_tag).model_dump()

    return jsonify(response)


@recipes_bp.route('/recipe-tags/<int:id>', methods=['PUT'])
@superuser_only
def update_recipe_tag(id: int):
    try:
        schema = RecipeTagUpdate(**request.get_json())
    except ValidationError as error:
        return jsonify({"errors": error.errors(include_url=False, include_context=False)}), 400
    
    tag = RecipeTag.query.filter_by(id=id).first_or_404()
    
    new_data = schema.model_dump(exclude_unset=True)
    for key, value in new_data.items():
        setattr(tag, key, value)
        
    errors = safe_commit(db, logger)
    if errors:
        return errors

    response = RecipeTagSchema.model_validate(tag).model_dump()

    return jsonify(response)


@recipes_bp.route('/recipe-tags/<int:id>', methods=['DELETE'])
@superuser_only
def delete_recipe_tag(id: int):
    tag = RecipeTag.query.filter_by(id=id).first()
    if not tag:
        abort(404)

    db.session.delete(tag)
    errors = safe_commit(db, logger)
    if errors:
        return errors

    return '', 204
