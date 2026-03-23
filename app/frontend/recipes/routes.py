from flask import Blueprint, abort, render_template
from flask_login import login_required

from backend.recipes.helpers import get_recipe_related_objects_cached
from backend.recipes.models import MealType, Recipe, RecipeTag
from backend.utils.login import is_owner_or_superuser


recipes_front_bp = Blueprint(
    name='recipes_frontend',
    import_name=__name__,
    template_folder='templates')


@recipes_front_bp.route('/', methods=['GET'])
def index_page():
    return render_template('recipes/index_page.html')

  
@recipes_front_bp.route('/search', methods=['GET'])
def search_page():
    return render_template('recipes/recipes/search_results.html')

    
@recipes_front_bp.route('/mix', methods=['GET'])
def mix_creation_page():
    context = get_recipe_related_objects_cached()
    return render_template('recipes/mixes/mix_creation_page.html', context=context)


@recipes_front_bp.route('/mixes', methods=['GET'])
@login_required
def mix_list_page():
    return render_template('recipes/mixes/my_mixes_page.html')


@recipes_front_bp.route('/mixes/<int:id>', methods=['GET'])
def mix_view_page(id: int):
    context = {
        'mix_id': id
    }
    return render_template('recipes/mixes/mix_page.html', context=context)


@recipes_front_bp.route('/my-recipes', methods=['GET'])
@login_required
def personal_recipe_list_page():
    return render_template('recipes/recipes/personal/personal_recipe_list.html')


@recipes_front_bp.route('/my-favs', methods=['GET'])
@login_required
def favorites_page():
    return render_template('recipes/recipes/personal/liked_recipe_list.html')


@recipes_front_bp.route('/recipes/<slug>', methods=['GET'])
def recipe_page(slug: str):
    recipe = Recipe.ua_query().filter_by(slug=slug).first()
    if not recipe:
        abort(404)
        
    if recipe.is_published:
        template_name = 'recipes/recipes/public_recipe.html'
    else:
        template_name = 'recipes/recipes/personal/personal_recipe.html'

    context = {
        "recipe": recipe
    }
    
    return render_template(template_name, context=context)
    

@recipes_front_bp.route('/recipes', methods=['GET'])
@login_required
def recipe_creation_page():
    context = get_recipe_related_objects_cached()
    return render_template('recipes/recipes/recipe_create.html', context=context)


@recipes_front_bp.route('/recipes/<slug>/edit', methods=['GET'])
@login_required
def recipe_edit_page(slug: str):    
    recipe = Recipe.ua_query().filter_by(slug=slug).first()
    if not recipe:
        abort(404)
    if not is_owner_or_superuser(recipe.author):
        abort(403)

    context = get_recipe_related_objects_cached()
    context['recipe'] = recipe
    context['recipe_tag_ids'] = {tag.id for tag in recipe.tags}
  
    return render_template('recipes/recipes/recipe_edit.html', context=context)
