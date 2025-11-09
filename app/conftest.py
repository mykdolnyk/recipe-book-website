import pytest
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