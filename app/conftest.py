from flask.testing import FlaskClient
import flask_login
import pytest
from backend.utils.fixtures import load_fixtures
from backend.recipes.models import Recipe, RecipePublicationApplication, RecipeTag
from backend.users.models import User
from backend.users.schemas import UserCreate
from backend.users.helpers import create_user_instance
from app_factory import create_app, db
import config
from click.testing import CliRunner


@pytest.fixture
def app():
    overrides = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///test.db"
    }
    app = create_app(config_object=config, overrides=overrides)

    with app.app_context():
        db.create_all()
        load_fixtures()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app) -> CliRunner:
    return app.test_cli_runner()


TEST_PASSWORD = 'r3p[avn!f;1cFGKDS'


@pytest.fixture
def test_users() -> dict[str, list[User]]:
    """Inserts into the DB a set of 10 active uses, 5 inactive users, 3 superusers"""
    users: dict[str, list[User]] = {
        "active": [],
        "inactive": [],
        "super": [],
    }

    # Create usual users:
    for num in range(10):
        schema = UserCreate(
            name=f'Usual User {num}',
            email=f'user{num}@test.com',
            password=TEST_PASSWORD,
            password_confirm=TEST_PASSWORD
        )
        user = create_user_instance(user_schema=schema)
        users['active'].append(user)

    # Create inactive users:
    for num in range(5):
        schema = UserCreate(
            name=f'Inactive User {num}',
            email=f'inactiveuser{num}@test.com',
            password=TEST_PASSWORD,
            password_confirm=TEST_PASSWORD
        )
        user = create_user_instance(user_schema=schema)
        user.is_active = False
        users['inactive'].append(user)
    db.session.commit()

    # Create superusers:
    for num in range(3):
        schema = UserCreate(
            name=f'Super User {num}',
            email=f'superuser{num}@test.com',
            password=TEST_PASSWORD,
            password_confirm=TEST_PASSWORD
        )
        user = create_user_instance(user_schema=schema)
        user.is_superuser = True
        users['super'].append(user)
    db.session.commit()

    return users


@pytest.fixture
def logged_in_user(app):
    schema = UserCreate(
        name='Logged In User',
        email='testing@test.com',
        password=TEST_PASSWORD,
        password_confirm=TEST_PASSWORD
    )
    user = create_user_instance(user_schema=schema)

    with app.test_request_context():
        flask_login.login_user(user)
        yield user


@pytest.fixture
def test_recipes(app):
    recipes: dict[str, list[Recipe]] = {
        'visible': [],
        'hidden': [],
    }

    # Visible recipes
    for num in range(10):
        recipe = Recipe(
            name=f"Visible Recipe {num}",
            calories="4",
            cooking_time="1337",
            ingredients="Water",
            text="A very long recipe here",
            meal_type_id=1,
            author_id=9999,
            slug=f"test-slug-visible-{num}",
            is_published=True
        )
        db.session.add(recipe)
        recipes['visible'].append(recipe)

    # Hidden recipes
    for num in range(5):
        recipe = Recipe(
            name=f"Visible Recipe {num}",
            calories="0",
            cooking_time="1337",
            ingredients="Water",
            text="A very long recipe here",
            meal_type_id=1,
            author_id=9999,
            slug=f"test-slug-hidden-{num}",
            is_visible=False
        )
        db.session.add(recipe)
        recipes['hidden'].append(recipe)

    db.session.commit()

    return recipes


@pytest.fixture
def test_recipe_tags(app):
    tags: dict[str, list[RecipeTag]] = {
        'visible': [],
    }

    for num in range(10):
        recipe = RecipeTag(
            name=f"Recipe Tag {num}",
            slug=f"test-slug-{num}"
        )
        db.session.add(recipe)
        tags['visible'].append(recipe)

    db.session.commit()

    return tags


@pytest.fixture
def testing_setup(client: FlaskClient, monkeypatch) -> dict:
    objects = {
        'users': {
            "active": [],
            "inactive": [],
            "super": []
        },
        'recipes': {
            'published': [],
            'personal': [],
            'hidden': [],
        },
        'recipe_tags': [],
        'recipe_pub_apps': [],
    }
    
    # ----- Change hashing for testing purposes -----
    
    def fake_hash(password, salt):
        return f"fake-hash-{password.decode()}".encode()

    def fake_check(password, hashed_password):
        return hashed_password == fake_hash(password, None)

    monkeypatch.setattr("bcrypt.hashpw", fake_hash)
    monkeypatch.setattr("bcrypt.checkpw", fake_check)

    # ----- Create Users -----

    # Create usual active users:
    for num in range(10):
        schema = UserCreate(
            name=f'Usual User {num}',
            email=f'user{num}@test.com',
            password=TEST_PASSWORD,
            password_confirm=TEST_PASSWORD
        )
        user = create_user_instance(user_schema=schema)
        objects['users']['active'].append(user)
    # Create inactive users:
    for num in range(5):
        schema = UserCreate(
            name=f'Inactive User {num}',
            email=f'inactiveuser{num}@test.com',
            password=TEST_PASSWORD,
            password_confirm=TEST_PASSWORD
        )
        user = create_user_instance(user_schema=schema)
        user.is_active = False
        objects['users']['inactive'].append(user)
    # Create superusers:
    for num in range(3):
        schema = UserCreate(
            name=f'Super User {num}',
            email=f'superuser{num}@test.com',
            password=TEST_PASSWORD,
            password_confirm=TEST_PASSWORD
        )
        user = create_user_instance(user_schema=schema)
        user.is_superuser = True
        objects['users']['super'].append(user)
        
    db.session.flush()
        
    # ----- Create Recipe Tags -----
    
    for num in range(10):
        tag = RecipeTag(
            name=f"Recipe Tag {num}",
            slug=f"test-slug-{num}"
        )
        db.session.add(tag)
        objects['recipe_tags'].append(tag)
        
    db.session.flush()
        
    # ----- Create Recipes -----
    
    # Published recipes
    for num in range(10):
        recipe = Recipe(
            name=f"Visible Recipe {num}",
            calories="4",
            cooking_time="1337",
            ingredients="Water",
            text="A very long recipe here",
            meal_type_id=1,
            author_id=objects['users']['active'][num].id,  # <- the recipe is owned by 
            slug=f"test-slug-published-{num}",             # the corresponding user 
            is_published=True,
            is_visible=True,
        )
        db.session.add(recipe)
        objects['recipes']['published'].append(recipe)

    # Personal recipes (visible but not published)
    for num in range(10):
        recipe = Recipe(
            name=f"Visible Recipe {num}",
            calories="4",
            cooking_time="1337",
            ingredients="Water",
            text="A very long recipe here",
            meal_type_id=1,
            author_id=objects['users']['active'][num].id,  # <- the recipe is owned by 
            slug=f"test-slug-personal-{num}",              # the corresponding user 
            is_published=False,
            is_visible=True,
        )
        db.session.add(recipe)
        objects['recipes']['personal'].append(recipe)
        
    # Hidden recipes
    for num in range(5):
        recipe = Recipe(
            name=f"Hidden Recipe {num}",
            calories="0",
            cooking_time="1337",
            ingredients="Water",
            text="A very long recipe here",
            meal_type_id=1,
            author_id=objects['users']['active'][num].id,  # <- the recipe is owned by 
            slug=f"test-slug-hidden-{num}",             # the corresponding user 
            is_published=True,
            is_visible=False,
        )
        db.session.add(recipe)
        objects['recipes']['hidden'].append(recipe)
        
    db.session.flush()

    # ----- Create Recipe Publication Applications -----
        
    for num in range(5):
        application = RecipePublicationApplication(
            recipe_id=objects['recipes']['published'][num].id,
            comment=f'Comment num {num}'
        )
        db.session.add(application)
        objects['recipe_pub_apps'].append(application)

    db.session.commit()

    return objects
