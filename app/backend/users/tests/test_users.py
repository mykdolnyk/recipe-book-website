from flask.testing import FlaskClient
from werkzeug.test import TestResponse
from app.backend.utils.errors import ErrorCode
from backend.users.models import User
from conftest import TEST_PASSWORD


def test_register_user(client: FlaskClient):
    user_name = 'testing'
    email = "test@example.com"

    response = client.post('/api/users', json={
        "name": user_name,
        "email": email,
        "password": TEST_PASSWORD,
        "password_confirm": TEST_PASSWORD,
    })
    assert response.status_code == 200
    assert response.json['name'] == user_name
    assert User.active().filter_by(email=email).first()

    # create the same user
    response = client.post('/api/users', json={
        "name": user_name,
        "email": email,
        "password": TEST_PASSWORD,
        "password_confirm": TEST_PASSWORD,
    })
    assert response.status_code == 400
    assert User.active().filter_by(email=email).count() == 1

    # create different user
    new_email = 'not' + email
    response = client.post('/api/users', json={
        "name": user_name,
        "email": new_email,
        "password": TEST_PASSWORD,
        "password_confirm": TEST_PASSWORD,
    })
    assert response.status_code == 200
    assert User.active().filter_by(email=new_email)


def test_login_user(client: FlaskClient, test_users):
    user = test_users['active'][0]
    response = client.post('/api/auth/login', json={
        "email": user.email,
        "password": TEST_PASSWORD,
    })

    assert response.status_code == 200
    with client.session_transaction() as session:
        assert '_user_id' in session

    # log in again to the same account
    response = client.post('/api/auth/login', json={
        "email": user.email,
        "password": TEST_PASSWORD,
    })
    assert response.status_code == 400
    with client.session_transaction() as session:
        assert '_user_id' in session


def test_logout_user(client: FlaskClient, test_users):
    user = test_users['active'][0]
    # log in first
    response = client.post('/api/auth/login', json={
        "email": user.email,
        "password": TEST_PASSWORD,
    })

    # ensure the client was logged in before
    assert response.status_code == 200
    with client.session_transaction() as session:
        assert '_user_id' in session

    # log out
    response = client.post('/api/auth/logout')

    assert response.status_code == 200
    with client.session_transaction() as session:
        assert '_user_id' not in session

    # log out again (without a session)
    response = client.post('/api/auth/logout')

    assert response.status_code == 200
    with client.session_transaction() as session:
        assert '_user_id' not in session


def test_delete_user(client: FlaskClient, test_users):
    user = test_users['active'][0]
    superuser = test_users['super'][0]
    other_user = test_users['active'][1]
    # non-logged in user tries to delete
    response = client.delete(f'/api/users/{user.id}?confirm=True')
    assert response.status_code == 403
    assert User.active().filter_by(email=user.email).first()

    # log in
    response = client.post('/api/auth/login', json={
        "email": user.email,
        "password": TEST_PASSWORD,
    })
    # non-confirmed delete
    response = client.delete(f'/api/users/{user.id}')
    assert response.status_code == 403
    assert User.active().filter_by(email=user.email).first()
    # confirmed delete
    response = client.delete(f'/api/users/{user.id}?confirm=True')
    assert response.status_code == 204
    assert not User.active().filter_by(email=user.email).first()

    # restore the user
    user.is_active = True
    User.query.session.commit()
    assert User.active().filter_by(email=user.email).first()
    # log out and log in as a superuser
    response = client.post('/api/auth/logout')
    response = client.post('/api/auth/login', json={
        "email": superuser.email,
        "password": TEST_PASSWORD,
    })
    # delete as a superuser
    response = client.delete(f'/api/users/{user.id}?confirm=True')
    assert response.status_code == 204
    assert not User.active().filter_by(email=user.email).first()
    
    # restore the user
    user.is_active = True
    User.query.session.commit()
    assert User.active().filter_by(email=user.email).first()
    # log out and log in as a non-owner non-superuser
    response = client.post('/api/auth/logout')
    response = client.post('/api/auth/login', json={
        "email": other_user.email,
        "password": TEST_PASSWORD,
    })
    # delete as non-owner non-superuser
    response = client.delete(f'/api/users/{user.id}?confirm=True')
    assert response.status_code == 403
    assert User.active().filter_by(email=user.email).first()


def test_edit_user(client: FlaskClient, test_users):
    user = test_users['active'][0]
    superuser = test_users['super'][0]
    other_user = test_users['active'][1]
    new_name = 'beb'
    # non-logged in user tries to edit
    response = client.put(f'/api/users/{user.id}', json={
        'name': new_name
    })
    assert response.status_code == 403
    assert not User.active().filter_by(name=new_name).first()

    # log in
    response = client.post('/api/auth/login', json={
        "email": user.email,
        "password": TEST_PASSWORD,
    })
    # logged-in update
    response = client.put(f'/api/users/{user.id}', json={
        'name': new_name
    })
    assert response.status_code == 200
    assert User.active().filter_by(name=new_name).first()

    # log out and log in as a superuser
    response = client.post('/api/auth/logout')
    response = client.post('/api/auth/login', json={
        "email": superuser.email,
        "password": TEST_PASSWORD,
    })
    # update as a superuser
    newest_name = 'rak'
    response = client.put(f'/api/users/{user.id}', json={
        'name': newest_name
    })
    assert response.status_code == 200
    assert User.active().filter_by(name=newest_name).first()
    
    # log out and log in as a non-owner non-superuser
    response = client.post('/api/auth/logout')
    response = client.post('/api/auth/login', json={
        "email": other_user.email,
        "password": TEST_PASSWORD,
    })
    # update as non-owner non-superuser
    response = client.put(f'/api/users/{user.id}', json={
        'name': new_name
    })
    assert response.status_code == 403
    assert not User.active().filter_by(name=new_name).first()


def test_get_user(client: FlaskClient, test_users):
    user = test_users['active'][0]
    inactive_user = test_users['inactive'][0]
    response: TestResponse = client.get(f'/api/users/{user.id}')
    assert response.status_code == 200
    assert response.get_json()['name'] == user.name
    assert not response.get_json().get('email')

    # inactive user 
    response = client.get(f'/api/users/{inactive_user.id}')
    assert response.status_code == 400
    assert response.get_json()['errors'][0]['msg'] == ErrorCode.USER_NOT_FOUND.value
    
    # non-existent user 
    response = client.get(f'/api/users/9999')
    assert response.status_code == 400
    

def test_get_user_list(client: FlaskClient, test_users):
    response: TestResponse = client.get('/api/users')
    assert response.status_code == 200
    assert response.get_json()['total'] == 13 # Number of users created by the fixture, excluding inactive ones
    # Checking pagination
    assert response.get_json()['per_page'] == 5
    assert response.get_json()['pages'] == 3

    # Exceeding max per page
    response: TestResponse = client.get('/api/users?per-page=30')
    assert response.status_code == 200
    assert response.get_json()['per_page'] == 25
    assert response.get_json()['pages'] == 1
    
    # Incorrect params
    response: TestResponse = client.get('/api/users?per-page=hello')
    assert response.status_code == 400

