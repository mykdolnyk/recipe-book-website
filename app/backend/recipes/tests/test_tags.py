from flask.testing import FlaskClient
from conftest import TEST_PASSWORD


def test_create_tag(app, client: FlaskClient, test_user, test_superuser):
    # logged-out request
    name = "Tag name"
    response = client.post('/api/recipe-tags', json={
        "name": name,
    })
    assert response.status_code == 401

    # logged in as a usual user
    response = client.post('/api/auth/login', json={
        "email": test_user.email,
        "password": TEST_PASSWORD,
    })
    response = client.post('/api/recipe-tags', json={
        "name": name,
    })
    assert response.status_code == 403

    # logged in as a superuser
    response = client.post('/api/auth/logout')
    response = client.post('/api/auth/login', json={
        "email": test_superuser.email,
        "password": TEST_PASSWORD,
    })
    response = client.post('/api/recipe-tags', json={
        "name": name,
    })
    assert response.status_code == 200
    assert response.get_json()['name'] == name


def test_edit_tag(client: FlaskClient, test_user, test_superuser, test_recipe_tags):
    tag = test_recipe_tags['visible'][0]
    new_name = "New Tag"
    assert tag.name != new_name

    # non-logged-in request
    response = client.put(f'/api/recipe-tags/{tag.id}', json={
        "name": new_name,
    })
    assert response.status_code == 401

    # non-superuser logged-in request
    response = client.post('/api/auth/login', json={
        "email": test_user.email,
        "password": TEST_PASSWORD,
    })
    response = client.put(f'/api/recipe-tags/{tag.id}', json={
        "name": new_name,
    })
    assert response.status_code == 403

    # superuser request
    response = client.post('/api/auth/logout')
    response = client.post('/api/auth/login', json={
        "email": test_superuser.email,
        "password": TEST_PASSWORD,
    })
    response = client.put(f'/api/recipe-tags/{tag.id}', json={
        "name": new_name,
    })
    assert response.status_code == 200
    assert response.get_json()['name'] == new_name


def test_get_tag(client: FlaskClient, test_recipe_tags):
    tag = test_recipe_tags['visible'][0]

    # get a tag
    response = client.get(f'/api/recipe-tags/{tag.id}')
    assert response.status_code == 200
    assert response.get_json()['name'] == tag.name

    # get unexistent tag
    unexistent_tag_id = 9999
    response = client.get(f'/api/recipe-tags/{unexistent_tag_id}')
    assert response.status_code == 404


def test_get_tag_list(client: FlaskClient, test_recipe_tags):
    response = client.get('/api/recipe-tags')
    assert response.status_code == 200
    assert response.get_json()["total"] == len(test_recipe_tags['visible'])

    # Checking pagination
    assert response.get_json()['per_page'] == 5
    assert response.get_json()['pages'] == 2
    # Exceeding max per page
    response = client.get('/api/recipe-tags?per-page=30')
    assert response.status_code == 200
    assert response.get_json()['per_page'] == 25
    assert response.get_json()['pages'] == 1
    # Incorrect params
    response = client.get('/api/recipe-tags?per-page=hello')
    assert response.status_code == 400


def test_delete_tag(client: FlaskClient, test_user, test_superuser, test_recipe_tags):
    tag = test_recipe_tags['visible'][0]

    # non-logged-in request
    response = client.delete(f'/api/recipe-tags/{tag.id}')
    assert response.status_code == 401

    # non-superuser logged-in request
    response = client.post('/api/auth/login', json={
        "email": test_user.email,
        "password": TEST_PASSWORD,
    })
    response = client.delete(f'/api/recipe-tags/{tag.id}')
    assert response.status_code == 403

    # superuser request
    response = client.post('/api/auth/logout')
    response = client.post('/api/auth/login', json={
        "email": test_superuser.email,
        "password": TEST_PASSWORD,
    })
    response = client.delete(f'/api/recipe-tags/{tag.id}')
    assert response.status_code == 204
