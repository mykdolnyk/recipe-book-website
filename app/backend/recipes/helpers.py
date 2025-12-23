import random
from app_factory import db
from sqlalchemy import func
from backend.recipes.models import MealType, Recipe, RecipeMix, RecipeTag
from backend.users.models import User
from backend.utils.name_generation import recipe_mix_names


def create_recipe_mix(include_tags: list[int] = None, exclude_tags: list[int] = None,
                      max_calories: int | None = None, min_calories: int | None = None,
                      meal_type_ids: list[int] = None,
                      personal_only: bool = False, public_only: bool = False,
                      author: User = None):

    if (include_tags and exclude_tags) or (personal_only and public_only):
        raise ValueError('Conflicting parameters were provided.')
    if not meal_type_ids:
        raise ValueError('Meal Types were not specified.')

    recipe_query = Recipe.ua_query(user=author)

    # Calories
    if max_calories is not None:
        recipe_query = recipe_query.filter(Recipe.calories <= max_calories)
    if min_calories is not None:
        recipe_query = recipe_query.filter(Recipe.calories >= min_calories)

    # Tags
    if include_tags:
        recipe_query = recipe_query.filter(
            Recipe.tags.any(RecipeTag.id.in_(include_tags)))
    elif exclude_tags:
        recipe_query = recipe_query.filter(
            ~Recipe.tags.any(RecipeTag.id.in_(exclude_tags)))

    # Personal/public only
    if personal_only:
        recipe_query = recipe_query.filter(Recipe.is_published.is_(False))
    elif public_only:
        recipe_query = recipe_query.filter(Recipe.is_published.is_(True))

    meal_types: list[MealType] = MealType.query.filter(
        MealType.id.in_(meal_type_ids)).all()

    recipe_list = []
    for meal_type in meal_types:

        subquery = recipe_query.filter(
            Recipe.meal_type == meal_type).with_entities(Recipe.id).subquery()

        min_id, max_id = db.session.query(
            func.min(subquery.c.id),
            func.max(subquery.c.id)
        ).one()

        if min_id is None:
            # If no objects fit the criteria: skip
            continue

        random_id = random.randint(min_id, max_id)

        recipe_list.append(recipe_query
                           .filter(Recipe.meal_type == meal_type)
                           .filter(Recipe.id >= random_id)
                           .order_by(Recipe.id)
                           .first()
                           )

    recipe_name = generate_recipe_mix_name()
    recipe_mix = RecipeMix(
        name=recipe_name,
        author_id=author.id
    )
    recipe_mix.recipes = recipe_list
    
    db.session.add(recipe_mix)
    db.session.commit()

    return recipe_mix


def generate_recipe_mix_name(adjectives_num=1):
    name = random.choice(recipe_mix_names.nouns)
    for i in range(adjectives_num):
        name = f"{random.choice(recipe_mix_names.adjectives)} {name}".title()
    return name
