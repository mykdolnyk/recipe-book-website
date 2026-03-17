import json
from app_factory import redis_client
from celery import shared_task
from backend.recipes.helpers import get_popular_recipes_query


@shared_task(ignore_result=False)
def calculate_popular_recipes():
    popular_recipes = get_popular_recipes_query().all()
    recipe_id_list = [obj.id for obj in popular_recipes]
    redis_client.set(
        name='popular_recipes',
        value=json.dumps(recipe_id_list)
    )
