from datetime import timedelta
from celery import Celery
from app_factory import create_app, redis_client
from backend.recipes.tasks import calculate_popular_recipes

flask_app = create_app()
celery_app: Celery = flask_app.extensions["celery"]

celery_app.autodiscover_tasks(['backend.recipes', 'backend.users'])

LOCK_EXPIRE = 60 # seconds


# Periodic Tasks
@celery_app.on_after_finalize.connect
def add_periodic_tasks(sender: Celery, **kwargs):
    sender.add_periodic_task(
        timedelta(minutes=1),
        # The 1-minute period is for demonstrational purposes only
        calculate_popular_recipes.s(),
        name='calculate popular recipes')


# Tasks on Startup
@celery_app.on_after_finalize.connect
def run_tasks_on_startup(sender: Celery, **kwargs):
    task_list = [
        calculate_popular_recipes
    ]
    
    for task in task_list:
        lock_id = f'lock:{task.__name__}'
        lock = redis_client.get(lock_id)
        if lock is None:
            task.delay()
            redis_client.set(lock_id, 1, LOCK_EXPIRE)
