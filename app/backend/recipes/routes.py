from logging import getLogger
from flask.blueprints import Blueprint
from flask import abort, json, jsonify, request
from flask_login import login_required
from pydantic import ValidationError
from backend.utils.misc import safe_commit
from backend.utils.errors import ErrorCode, create_error_response
from backend.utils.login import is_owner_or_superuser, superuser_only
from backend.utils.pagination import paginate
from backend.recipes.helpers import create_recipe_instance
from backend.recipes.models import PeriodType, Recipe, RecipeTag
from backend.recipes.schemas import PeriodTypeSchema, RecipeCreate, RecipeUpdate, RecipeSchema, RecipeTagCreate, RecipeTagSchema, RecipeTagUpdate
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
    pagination = paginate(
        request_args=request.args,
        sqlalchemy_query=Recipe.visible(),
        pydantic_model=RecipeSchema,
        list_name='recipe_list',
    )

    return jsonify(pagination)


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

    if not is_owner_or_superuser(recipe.author):
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

    if not is_owner_or_superuser(recipe.author):
        abort(403)

    recipe.is_visible = False
    errors = safe_commit(db, logger)
    if errors:
        return errors

    return '', 204


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


@recipes_bp.route('/recipe-types/', methods=['GET'])
def get_recipe_type_list():
    # todo: cache aggresively
    pagination = paginate(
        request_args=request.args,
        sqlalchemy_query=PeriodType.query,
        pydantic_model=PeriodTypeSchema,
        list_name='period_type_list',
    )

    return jsonify(pagination)


@recipes_bp.route('/recipe-types/<int:id>', methods=['GET'])
def get_recipe_type(id: int):
    rtype = PeriodType.visible().filter_by(id=id).first()
    if not rtype:
        abort(404)

    response = PeriodTypeSchema.model_validate(rtype).model_dump()
    return jsonify(response)


