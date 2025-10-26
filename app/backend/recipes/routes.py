from logging import getLogger
from flask.blueprints import Blueprint
from flask import abort, json, jsonify, request
from pydantic import ValidationError
from backend.utils.errors import ErrorCode, create_error_response
from backend.recipes.helpers import create_recipe_instance
from backend.recipes.models import Recipe
from backend.recipes.schemas import RecipeCreate, RecipeEdit, RecipeSchema
from app_factory import db


logger = getLogger(__name__)


recipes_bp = Blueprint(
    name='recipes',
    import_name=__name__,
    url_prefix='/api',
)


@recipes_bp.route('/recipes', methods=['POST'])
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
def get_recipes_list():
    page = request.args.get('page', 0)
    per_page = request.args.get('per-page', 5)

    pagination = Recipe.query.paginate(page=page,
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
    recipe = Recipe.query.get(id)
    if not recipe:
        abort(404)

    response = RecipeSchema.model_validate(recipe).model_dump()
    return jsonify(response)


@recipes_bp.route('/recipes/<int:id>', methods=['PUT'])
def edit_recipe(id: int):
    try:
        recipe_schema = RecipeEdit(**request.get_json())
    except ValidationError as error:
        return jsonify({"errors": error.errors(include_url=False, include_context=False)}), 400

    recipe = Recipe.query.get(id)
    if not recipe:
        abort(404)

    new_data = recipe_schema.model_dump(exclude_unset=True)
    # Update the values of the DB model
    for key, value in new_data.items():
        setattr(recipe, key, value)

    try:
        db.session.commit()
    except Exception as e:
        logger.exception(e)
        return create_error_response(ErrorCode.UNKNOWN)

    response = RecipeSchema.model_validate(recipe).model_dump()

    return jsonify(response)
