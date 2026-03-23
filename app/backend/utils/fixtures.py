import json
from backend.users.models import ProfilePicture, User
import config
from backend.recipes.models import MealType, Recipe, RecipeTag
from app_factory import db


def load_fixtures():
    total_entries_pasted = 0
    total_entries_skipped = 0

    # Meal Types
    with open(config.FIXTURES_DIR / 'mealtypes.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    for entry in data:
        meal_type = MealType(**entry)
        if MealType.query.filter(MealType.id == meal_type.id).first():
            total_entries_skipped += 1
        else:
            db.session.add(meal_type)
            total_entries_pasted += 1

    # Recipe Tags
    with open(config.FIXTURES_DIR / 'recipetags.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    for entry in data:
        recipe_tag = RecipeTag(**entry)
        if RecipeTag.query.filter(RecipeTag.id == recipe_tag.id).first():
            total_entries_skipped += 1
        else:
            db.session.add(recipe_tag)
            total_entries_pasted += 1
    
    # Profile Pictures
    with open(config.FIXTURES_DIR / 'profilepictures.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    for entry in data:
        profile_picture = ProfilePicture(**entry)
        if ProfilePicture.query.filter(ProfilePicture.id == profile_picture.id).first():
            total_entries_skipped += 1
        else:
            db.session.add(profile_picture)
            total_entries_pasted += 1

    db.session.commit()
    
    # --- Load the example fixtures (for project demonstration) ---
    if config.LOAD_EXAMPLE_FIXTURES:
        # Users
        with open(config.FIXTURES_DIR / 'example' / 'exampleusers.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        for entry in data:
            user = User(**entry)
            if User.query.filter(User.id == user.id).first():
                total_entries_skipped += 1
            else:
                db.session.add(user)
                total_entries_pasted += 1
                
        # Recipes
        with open(config.FIXTURES_DIR / 'example' / 'examplerecipes.json', 'r', encoding='utf-8') as f:
            data = json.load(f)

        for entry in data:
            recipe = Recipe(**entry)
            if Recipe.query.filter(Recipe.id == recipe.id).first():
                total_entries_skipped += 1
            else:
                db.session.add(recipe)
                total_entries_pasted += 1
                
    db.session.commit()
    
    return {
        'total_entries_pasted': total_entries_pasted,
        'total_entries_skipped': total_entries_skipped
    }
    
    