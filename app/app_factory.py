from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_object):
    app = Flask(__name__)
    app.config.from_object(config_object)

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

    return app
