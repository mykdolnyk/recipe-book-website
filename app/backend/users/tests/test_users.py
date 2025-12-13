from flask.testing import FlaskClient
from werkzeug.test import TestResponse
from backend.utils.errors import ErrorCode
from backend.users.models import User
from conftest import TEST_PASSWORD
from flask_login import login_user


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


def test_login_user(client: FlaskClient, testing_setup):
    user = testing_setup['users']['active'][0]
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


def test_logout_user(client: FlaskClient, testing_setup):
    user = testing_setup['users']['active'][0]
    
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


def test_delete_user(client: FlaskClient, app, testing_setup):
    user = testing_setup['users']['active'][0]
    other_user = testing_setup['users']['active'][1]
    superuser = testing_setup['users']['super'][0]
    
    # non-logged in user tries to delete
    response = client.delete(f'/api/users/{user.id}?confirm=True')
    assert response.status_code == 403
    assert User.active().filter_by(email=user.email).first()

    # delete as non-owner non-superuser
    with app.test_request_context():
        login_user(other_user)
        
    response = client.delete(f'/api/users/{user.id}?confirm=True')
    assert response.status_code == 403
    assert User.active().filter_by(email=user.email).first()

    # delete as an owner user
    with app.test_request_context():
        login_user(user)
        
    # non-confirmed delete
    response = client.delete(f'/api/users/{user.id}')
    assert response.status_code == 403
    assert User.active().filter_by(email=user.email).first()
    
    # confirmed delete
    response = client.delete(f'/api/users/{user.id}?confirm=True')
    assert response.status_code == 204
    assert not User.active().filter_by(email=user.email).first()

    # restore the user for further testing
    user.is_active = True
    User.query.session.commit()
    assert User.active().filter_by(email=user.email).first()
    
    # delete as a superuser
    with app.test_request_context():
        login_user(superuser)

    response = client.delete(f'/api/users/{user.id}?confirm=True')
    assert response.status_code == 204
    assert not User.active().filter_by(email=user.email).first()


def test_edit_user(client: FlaskClient, app, testing_setup):
    user = testing_setup['users']['active'][0]
    other_user = testing_setup['users']['active'][1]
    superuser = testing_setup['users']['super'][0]

    new_name = 'A new name'
    
    # non-logged-in update
    response = client.put(f'/api/users/{user.id}', json={
        'name': new_name
    })
    assert response.status_code == 403
    assert not User.active().filter_by(name=new_name).first()

    # update as non-owner non-superuser
    with app.test_request_context():
        login_user(other_user)
    
    response = client.put(f'/api/users/{user.id}', json={
        'name': new_name
    })
    assert response.status_code == 403
    assert not User.active().filter_by(name=new_name).first()

    # logged-in update
    with app.test_request_context():
        login_user(user)
        
    response = client.put(f'/api/users/{user.id}', json={
        'name': new_name
    })
    assert response.status_code == 200
    assert User.active().filter_by(name=new_name).first()

    # update as a superuser
    with app.test_request_context():
        login_user(superuser)

    new_name = 'An even newer name'
    response = client.put(f'/api/users/{user.id}', json={
        'name': new_name
    })
    assert response.status_code == 200
    assert User.active().filter_by(name=new_name).first()


def test_get_user(client: FlaskClient, testing_setup):
    user = testing_setup['users']['active'][0]
    inactive_user = testing_setup['users']['inactive'][0]
    
    response: TestResponse = client.get(f'/api/users/{user.id}')
    assert response.status_code == 200
    assert response.get_json()['name'] == user.name
    assert not response.get_json().get('email')

    # inactive user 
    response = client.get(f'/api/users/{inactive_user.id}')
    assert response.status_code == 400
    assert response.get_json()['errors'][0]['msg'] == ErrorCode.USER_NOT_FOUND.value
    
    # non-existent user 
    response = client.get('/api/users/9999')
    assert response.status_code == 400
    

def test_get_user_list(client: FlaskClient, app, testing_setup):
    response: TestResponse = client.get('/api/users')
    assert response.status_code == 200
    assert response.get_json()['total'] == User.active().count()

    # admin request
    superuser = testing_setup['users']['super'][1]
    with app.test_request_context():
        login_user(superuser)
        
    response: TestResponse = client.get('/api/users')
    assert response.status_code == 200
    assert response.get_json()['total'] == User.query.count()