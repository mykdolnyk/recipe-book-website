from flask.testing import FlaskClient
from flask_login import login_user
from conftest import TEST_PASSWORD


def test_create_tag(client: FlaskClient, app, testing_setup):
    user = testing_setup['users']['active'][0]
    
    # logged-out request
    name = "Tag name"
    response = client.post('/api/recipe-tags', json={
        "name": name,
    })
    assert response.status_code == 401

    # logged in as a usual user
    with app.test_request_context():
        login_user(user)
    response = client.post('/api/recipe-tags', json={
        "name": name,
    })
    assert response.status_code == 403

    # logged in as a superuser
    user = testing_setup['users']['super'][0]
    with app.test_request_context():
        login_user(user)
    response = client.post('/api/recipe-tags', json={
        "name": name,
    })
    assert response.status_code == 200
    assert response.get_json()['name'] == name


def test_edit_tag(client: FlaskClient, app, testing_setup):
    tag = testing_setup['recipe_tags'][0]
    
    new_name = "New Tag Name"
    assert tag.name != new_name

    # non-logged-in request
    response = client.put(f'/api/recipe-tags/{tag.id}', json={
        "name": new_name,
    })
    assert response.status_code == 401

    # non-superuser logged-in request
    user = testing_setup['users']['active'][0]
    with app.test_request_context():
        login_user(user)

    response = client.put(f'/api/recipe-tags/{tag.id}', json={
        "name": new_name,
    })
    assert response.status_code == 403

    # superuser request
    user = testing_setup['users']['super'][0]
    with app.test_request_context():
        login_user(user)
        
    response = client.put(f'/api/recipe-tags/{tag.id}', json={
        "name": new_name,
    })
    assert response.status_code == 200
    assert response.get_json()['name'] == new_name


def test_get_tag(client: FlaskClient, testing_setup):
    tag = testing_setup['recipe_tags'][0]

    # get a tag
    response = client.get(f'/api/recipe-tags/{tag.id}')
    assert response.status_code == 200
    assert response.get_json()['name'] == tag.name

    # get unexistent tag
    unexistent_tag_id = 9999
    response = client.get(f'/api/recipe-tags/{unexistent_tag_id}')
    assert response.status_code == 404


def test_get_tag_list(client: FlaskClient, app, testing_setup):
    response = client.get('/api/recipe-tags')
    assert response.status_code == 200
    assert response.get_json()["total"] == len(testing_setup['recipe_tags'])


def test_delete_tag(client: FlaskClient, app, testing_setup):
    tag = testing_setup['recipe_tags'][0]

    # non-logged-in request
    response = client.delete(f'/api/recipe-tags/{tag.id}')
    assert response.status_code == 401

    # non-superuser logged-in request
    user = testing_setup['users']['active'][0]
    with app.test_request_context():
        login_user(user)

    response = client.delete(f'/api/recipe-tags/{tag.id}')
    assert response.status_code == 403

    # superuser request
    user = testing_setup['users']['super'][0]
    with app.test_request_context():
        login_user(user)

    response = client.delete(f'/api/recipe-tags/{tag.id}')
    assert response.status_code == 204
