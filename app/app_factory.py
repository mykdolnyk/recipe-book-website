from fakeredis import FakeRedis
from redis import Redis
from flask_redis import FlaskRedis

from backend.utils.anon_user import AnonymousUser
from backend.utils.login import authorization_context_processors, redirect_to_login_callback
from backend.utils.rate_limiting import setup_rate_limiting
import config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from password_strength import PasswordPolicy
from logging.config import dictConfig as logging_config
from celery import Celery, Task


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
password_policy = PasswordPolicy.from_names(**config.PASSWORD_POLICY)
redis_client: Redis = FlaskRedis()


def create_app(config_object=config, overrides=None):
    logging_config(config.LOGGING)

    # Flask Init
    app = Flask(
        __name__,
        static_url_path=config.STATIC_URL_PATH.as_posix(),
        template_folder="frontend/templates"
    )
    app.config.from_object(config_object)
    if overrides:
        app.config.update(overrides)

    db.init_app(app=app)
    migrate.init_app(app=app, db=db)
    login_manager.init_app(app=app)
    celery_init_app(app=app)
    redis_client.init_app(app=app)
    if app.testing:
        redis_client._redis_client = FakeRedis()

    # Models
    from backend.users.models import User
    from backend.recipes.models import (
        Recipe,
        RecipeMix,
        RecipePublicationApplication,
        RecipeTag,
        Like,
        MealType,
        recipe_mix_association,
        recipe_tag_association,
    )

    # Login 
    @login_manager.user_loader
    def user_loader(user_id: str):
        return User.query.get(int(user_id))
    login_manager.anonymous_user = AnonymousUser
    login_manager.unauthorized_handler(redirect_to_login_callback)    

    # CLI
    import backend.recipes.cli
    import backend.users.cli
    
    from backend.utils.cli import load_fixtures_command

    app.cli.add_command(load_fixtures_command)
    
    # Blueprints
    from backend.users.routes import user_bp
    from backend.recipes.routes import recipes_bp
    
    from frontend.recipes.routes import recipes_front_bp
    from frontend.users.routes import users_front_bp
    
    # Rate Limiting
    setup_rate_limiting(app=user_bp, redis_client=redis_client, testing=app.testing)
    setup_rate_limiting(app=recipes_bp, redis_client=redis_client, testing=app.testing)
    
    app.register_blueprint(user_bp)
    app.register_blueprint(recipes_bp)
    
    app.register_blueprint(recipes_front_bp)
    app.register_blueprint(users_front_bp)
    
    # Context Processors
    app.context_processor(authorization_context_processors)

    return app


def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config['CELERY_CONFIG'])
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app