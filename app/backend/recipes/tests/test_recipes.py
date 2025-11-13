from flask.testing import FlaskClient
from flask_login import current_user, login_user, logout_user

from backend.recipes.models import Recipe


def test_create_recipe(client: FlaskClient, logged_in_user):
    name = "Tasty meal"
    response = client.post('/api/recipes', json={
        "name": name,
        "calories": "4",
        "cooking_time": "1337",
        "ingredients": "Water",
        "text": "A very long recipe here",
        "period_type_id": 1,
    })
    assert response.status_code == 200
    assert response.get_json()['name'] == name
    assert response.get_json()['author']['id'] == current_user.id

    # logged-out request
    logout_user()
    response = client.post('/api/recipes', json={
        "name": name,
        "calories": "4",
        "cooking_time": "1337",
        "ingredients": "Water",
        "text": "A very long recipe here",
        "period_type_id": 1,
    })
    assert response.status_code == 401


def test_edit_recipe(client: FlaskClient, logged_in_user, test_recipes, test_users):
    superuser = test_users['super'][0]
    recipe = test_recipes["visible"][0]

    new_name = "Tasty meal"
    assert recipe.name != new_name

    recipe.author_id = logged_in_user.id
    Recipe.query.session.commit()
    response = client.put(f'/api/recipes/{recipe.id}', json={
        "name": new_name,
    })
    assert response.status_code == 200
    assert response.get_json()['name'] == new_name

    # logged-out request
    logout_user()
    new_name = "Forbidden meal"
    response = client.put(f'/api/recipes/{recipe.id}', json={
        "name": new_name,
    })
    assert response.status_code == 403

    # superuser request
    login_user(superuser)
    new_name = "Super meal"
    response = client.put(f'/api/recipes/{recipe.id}', json={
        "name": new_name,
    })
    assert response.status_code == 200
    assert response.get_json()['name'] == new_name
    assert response.get_json()['author']['id'] == logged_in_user.id


def test_get_recipe(client: FlaskClient, logged_in_user):
    # create a recipe
    name = 'Getting a Recipe'
    response = client.post('/api/recipes', json={
        "name": name,
        "calories": "4",
        "cooking_time": "1337",
        "ingredients": "Water",
        "text": "A very long recipe here",
        "period_type_id": 1,
    })

    recipe_id = response.get_json()['id']

    # get a recipe
    response = client.get(f'/api/recipes/{recipe_id}')
    assert response.status_code == 200
    assert response.get_json()['name'] == name

    # get a recipe with `is_visible` set to `False`
    recipe: Recipe = Recipe.query.filter_by(id=recipe_id).first()
    recipe.is_visible = False
    Recipe.query.session.commit()

    response = client.get(f'/api/recipes/{recipe_id}')
    assert response.status_code == 404
    # TODO: once recipe publication is implemented, test it


def test_get_recipe_list(client: FlaskClient, test_recipes):
    response = client.get('/api/recipes')
    assert response.status_code == 200
    assert response.get_json()["total"] == len(test_recipes['visible'])

    # Checking pagination
    assert response.get_json()['per_page'] == 5
    assert response.get_json()['pages'] == 2
    # Exceeding max per page
    response = client.get('/api/recipes?per-page=30')
    assert response.status_code == 200
    assert response.get_json()['per_page'] == 25
    assert response.get_json()['pages'] == 1
    # Incorrect params
    response = client.get('/api/recipes?per-page=hello')
    assert response.status_code == 400


def test_delete_recipe(client: FlaskClient, logged_in_user, test_recipes, test_users):
    superuser = test_users['super'][0]
    recipe = test_recipes["visible"][0]
    # wrong user:
    response = client.delete(f'/api/recipes/{recipe.id}')
    assert response.status_code == 403

    # correct user:
    recipe.author_id = logged_in_user.id
    Recipe.query.session.commit()
    response = client.delete(f'/api/recipes/{recipe.id}')
    assert response.status_code == 204
    response = client.get(f'/api/recipes/{recipe.id}')
    assert response.status_code == 404

    # un-delete the recipe and delete as a superuser
    recipe.is_visible = True
    Recipe.query.session.commit()
    logout_user()
    login_user(superuser)
    response = client.delete(f'/api/recipes/{recipe.id}')
    assert response.status_code == 204
    response = client.get(f'/api/recipes/{recipe.id}')
    assert response.status_code == 404
