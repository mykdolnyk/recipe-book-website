import pytest
from backend.users.models import User
from backend.users.schemas import UserCreate
from backend.users.helpers import create_user_instance
from app_factory import create_app, db
import config


@pytest.fixture
def app():
    overrides = {
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///test.db"
    }
    app = create_app(config_object=config, overrides=overrides)

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


TEST_PASSWORD = 'r3p[avn!f;1cFGKDS'


@pytest.fixture
def test_user():
    schema = UserCreate(
        name='Test User',
        email='testing@test.com',
        password=TEST_PASSWORD,
        password_confirm=TEST_PASSWORD
    )

    user = create_user_instance(user_schema=schema)

    return user


@pytest.fixture
def test_user_other():
    schema = UserCreate(
        name='Another Test User',
        email='testing2@test.com',
        password=TEST_PASSWORD,
        password_confirm=TEST_PASSWORD
    )

    user = create_user_instance(user_schema=schema)

    return user


@pytest.fixture
def test_inactive_user():
    schema = UserCreate(
        name='Inactive User',
        email='inactivetesting@test.com',
        password=TEST_PASSWORD,
        password_confirm=TEST_PASSWORD
    )

    user = create_user_instance(user_schema=schema)
    user.is_active = False
    db.session.commit()

    return user


@pytest.fixture
def test_superuser():
    schema = UserCreate(
        name='Super User',
        email='superuser@test.com',
        password=TEST_PASSWORD,
        password_confirm=TEST_PASSWORD
    )

    user = create_user_instance(user_schema=schema)
    user.is_superuser = True
    db.session.commit()

    return user


@pytest.fixture
def create_users() -> dict[str, list[User]]:
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
