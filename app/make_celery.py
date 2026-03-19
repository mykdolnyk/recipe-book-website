from datetime import timedelta
from celery import Celery
from app_factory import create_app
from backend.recipes.tasks import calculate_popular_recipes

flask_app = create_app()
celery_app: Celery = flask_app.extensions["celery"]

celery_app.autodiscover_tasks(['backend.recipes', 'backend.users'])

# Periodic Tasks
@celery_app.on_after_configure.connect
def run_tasks_on_startup(sender: Celery, **kwargs):
    sender.add_periodic_task(
        timedelta(minutes=1),
        # The 1-minute period is for demonstrational purposes only
        calculate_popular_recipes.s(),
        name='calculate popular recipes')
