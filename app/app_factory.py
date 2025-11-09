from backend.utils.anon_user import AnonymousUser
import config
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from password_strength import PasswordPolicy
from logging.config import dictConfig as logging_config


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
password_policy = PasswordPolicy.from_names(**config.PASSWORD_POLICY)


def create_app(config_object, overrides=None):
    logging_config(config.LOGGING)
    
    app = Flask(__name__)
    app.config.from_object(config_object)
    if overrides:
        app.config.update(overrides)

    db.init_app(app=app)
    migrate.init_app(app=app, db=db)
    login_manager.init_app(app=app)

    from backend.users.models import User
    from backend.recipes.models import (
        Recipe,
        RecipeMix,
        RecipePublicationApplication,
        RecipeTag,
        Like,
        PeriodType,
        recipe_mix_association,
        recipe_tag_association,
    )

    @login_manager.user_loader
    def user_loader(user_id: str):
        return User.query.get(int(user_id))
    login_manager.anonymous_user = AnonymousUser

    from backend.users.routes import user_bp
    from backend.recipes.routes import recipes_bp
    app.register_blueprint(user_bp)
    app.register_blueprint(recipes_bp)

    return app
