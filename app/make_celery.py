from datetime import timedelta
from celery import Celery
from app_factory import create_app
from backend.recipes.tasks import calculate_popular_recipes

flask_app = create_app()
celery_app: Celery = flask_app.extensions["celery"]

celery_app.autodiscover_tasks(['backend.recipes', 'backend.users'])

# Periodic Tasks
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender: Celery, **kwargs):
    sender.add_periodic_task(
        timedelta(hours=1),
        calculate_popular_recipes.s(),
        # "backend.recipes.tasks.calculate_popular_recipes",
        name='calculate popular recipes')
