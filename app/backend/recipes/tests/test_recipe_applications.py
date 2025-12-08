from flask import Flask
from flask.testing import FlaskClient
from flask_login import login_user

from backend.recipes.models import RecipePublicationApplication
from backend.users.models import User


def test_publish_recipe(client: FlaskClient, app: Flask, testing_setup: dict):
    recipe = testing_setup['recipes']['personal'][0]

    # Wrong user
    response = client.post(f'api/recipes/{recipe.id}/publish', json={
        "comment": "Some comment",
    })
    assert response.status_code == 404

    # Correct user
    with app.test_request_context():
        login_user(recipe.author)

    response = client.post(f'api/recipes/{recipe.id}/publish', json={
        "comment": "Some comment",
    })
    assert response.status_code == 200
    assert response.get_json()['recipe_id'] == recipe.id

    response = client.get(
        f'/api/recipes/applications/{response.get_json()['id']}')
    assert response.status_code == 200

    # Duplicate request
    response = client.post(f'api/recipes/{recipe.id}/publish', json={
        "comment": "Some comment",
    })
    assert response.status_code == 409

    # Alredy published recipe
    recipe.is_published = True
    recipe.query.session.commit()
    response = client.post(f'api/recipes/{recipe.id}/publish', json={
        "comment": "Some comment",
    })
    assert response.status_code == 400


def test_get_recipe_application(client: FlaskClient, app: Flask, testing_setup: dict):
    recipe_application: RecipePublicationApplication = testing_setup['recipe_pub_apps'][0]

    # Non-logged in
    response = client.get(f'/api/recipes/applications/{recipe_application.id}')
    assert response.status_code == 404

    # Correct user
    with app.test_request_context():
        login_user(recipe_application.recipe.author)

    response = client.get(f'/api/recipes/applications/{recipe_application.id}')
    assert response.status_code == 200
    assert response.get_json()['recipe_id'] == recipe_application.recipe_id

    # Wrong user
    # <- trying to take a non-related user
    user = testing_setup['users']['active'][1]
    assert user.id != recipe_application.recipe.author_id  # <- ensuring that
    with app.test_request_context():
        login_user(user)

    response = client.get(f'/api/recipes/applications/{recipe_application.id}')
    assert response.status_code == 404

    # Admin user
    user = testing_setup['users']['super'][0]
    assert user.id != recipe_application.recipe.author_id
    with app.test_request_context():
        login_user(user)

    response = client.get(f'/api/recipes/applications/{recipe_application.id}')
    assert response.status_code == 200


def test_get_recipe_application_list(client: FlaskClient, app: Flask, testing_setup: dict):
    # Non-logged in
    response = client.get(f'/api/recipes/applications')
    assert response.status_code == 401

    # Logged in
    user: User = testing_setup['users']['active'][0]
    with app.test_request_context():
        login_user(user)

    users_applications = RecipePublicationApplication.query.filter(
        RecipePublicationApplication.recipe.has(author_id=user.id)
    ).all()

    response = client.get(f'/api/recipes/applications')
    assert response.status_code == 200
    assert response.get_json()['total'] == len(users_applications)

    # Admin user
    user = testing_setup['users']['super'][0]
    with app.test_request_context():
        login_user(user)
        
    all_applications = RecipePublicationApplication.query.all()

    response = client.get(f'/api/recipes/applications')
    assert response.status_code == 200
    assert response.get_json()['total'] == len(all_applications)


def test_update_recipe_application(client: FlaskClient, app: Flask, testing_setup: dict):
    application: RecipePublicationApplication = testing_setup['recipe_pub_apps'][0]
    new_status = RecipePublicationApplication.STATUSES.ACCEPTED
    # Set the recipe as non-reviewed
    application.recipe.is_published = False
    application.query.session.commit()
    
    # non-logged-in request
    response = client.put(f'/api/recipes/applications/{application.id}', json={
        "status": new_status,
    })
    assert response.status_code == 401

    # non-superuser logged-in request
    user = testing_setup['users']['active'][0]
    with app.test_request_context():
        login_user(user)
        
    response = client.put(f'/api/recipes/applications/{application.id}', json={
        "status": new_status,
    }) 
    assert response.status_code == 403

    # superuser request
    user = testing_setup['users']['super'][0]
    with app.test_request_context():
        login_user(user)
        
    response = client.put(f'/api/recipes/applications/{application.id}', json={
        "status": new_status,
    }) 
    assert response.status_code == 200
    assert response.get_json()['status'] == new_status
    assert application.recipe.is_published


def test_update_recipe_status(client: FlaskClient, app: Flask, testing_setup: dict):
    recipe = testing_setup['recipes']['published'][0]
    new_is_published = False

    # non-logged-in request
    response = client.put(f'/api/recipes/{recipe.id}/status', json={
        "is_published": new_is_published,
    })
    assert response.status_code == 401

    # non-superuser logged-in request
    user = testing_setup['users']['active'][0]
    with app.test_request_context():
        login_user(user)
        
    response = client.put(f'/api/recipes/{recipe.id}/status', json={
        "is_published": new_is_published,
    }) 
    assert response.status_code == 403

    # superuser request
    user = testing_setup['users']['super'][0]
    with app.test_request_context():
        login_user(user)
        
    response = client.put(f'/api/recipes/{recipe.id}/status', json={
        "is_published": new_is_published,
    }) 
    assert response.status_code == 200
    assert response.get_json()['is_published'] == new_is_published
    assert recipe.is_published == new_is_published