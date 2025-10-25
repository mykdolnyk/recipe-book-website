from backend.recipes.schemas import RecipeCreate
from backend.recipes.models import Recipe
from app_factory import db


def create_recipe_instance(recipe_schema: RecipeCreate, commit=True):
    recipe_data: dict = recipe_schema.model_dump()
    
    new_recipe = Recipe(**recipe_data)
    
    if commit:
        db.session.add(new_recipe)
        db.session.commit()
    
    return new_recipe