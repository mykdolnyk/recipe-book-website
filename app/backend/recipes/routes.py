from flask.blueprints import Blueprint
from flask import abort, jsonify, request
from backend.recipes.models import Recipe


recipes_bp = Blueprint(
    name='recipes',
    import_name=__name__,
    url_prefix='/api',
)


@recipes_bp.route('/recipes', methods=['GET'])
def get_recipes_list():
    page = request.args.get('page', 0)
    per_page = request.args.get('per-page', 5)

    recipe_list = Recipe.query.paginate(page=page,
                                        per_page=per_page,
                                        max_per_page=25,
                                        error_out=False)
    if len(recipe_list.items) <= 1:
        recipe_list = []

    return recipe_list


@recipes_bp.route('/recipes/<int:id>', methods=['GET'])
def get_recipe(id: int):
    recipe = Recipe.query.get(id)

    if not recipe:
        abort(404)

    return jsonify(recipe)


@recipes_bp.route('/recipes', methods=['POST'])
def create_recipe():
    return 'OK', 200