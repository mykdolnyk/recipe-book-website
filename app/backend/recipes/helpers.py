import random

from app_factory import db
from sqlalchemy import and_, case, desc, func, or_
from sqlalchemy.orm import Query
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


def search_recipes(request_args) -> Query:
    query = Recipe.published()
    
    # Meal Types
    meal_types: list[int] = request_args.getlist('meal-types', type=int)
    if meal_types:
        query = query.filter(Recipe.meal_type_id.in_(meal_types))
    
    # Tags
    recipe_tags: list[int] = request_args.getlist('recipe-tags', type=int)
    if recipe_tags:
        query = query.join(Recipe.tags).filter(RecipeTag.id.in_(recipe_tags))
    
    query_text: str = request_args.get('text')
    if not query_text:
        return query

    words = query_text.lower().split()

    # Define score. Full string match will grant the highest score
    score = case(
        (
            Recipe.name.ilike(f"%{' '.join(words)}%"),
            5
        ),
        else_=0
    )

    filters = []
    for word in words:
        match_word = f'%{word}%'  # % for partial match

        # Add the score
        score += (
            case((Recipe.name.ilike(match_word), 3), else_=0)
            + case((Recipe.ingredients.ilike(match_word), 2), else_=0)
            + case((Recipe.description.ilike(match_word), 1), else_=0)
        )

        # Add the filter condition to the list to be applied later
        filters.append(
            or_(
                Recipe.name.ilike(match_word),
                Recipe.ingredients.ilike(match_word),
                Recipe.description.ilike(match_word),
            )
        )

    query = query.filter(*filters).distinct().order_by(desc(score))
    # distinct() to prevent duplicates

    return query
