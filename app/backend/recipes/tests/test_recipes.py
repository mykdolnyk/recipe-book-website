from flask.testing import FlaskClient
from flask_login import login_user, logout_user
from sqlalchemy import and_, or_

from backend.recipes.models import Recipe


def test_create_recipe(client: FlaskClient, app, testing_setup):
    user = testing_setup['users']['active'][0]
    data = {
        "name": "Tasty meal",
        "calories": 4,
        "cooking_time": 1337,
        "ingredients": "Water",
        "text": "A very long recipe here",
        "description": "A description",
        "meal_type_id": 1,
        'tags': [1, 2]
    }

    # non-logged in request
    response = client.post('/api/recipes', json=data)
    assert response.status_code == 401

    # logged in request
    with app.test_request_context():
        login_user(user)

    response = client.post('/api/recipes', json=data)
    assert response.status_code == 200
    assert response.get_json()['name'] == data['name']
    assert response.get_json()['author']['id'] == user.id
    
    # test with a None description
    data['description'] = None
    response = client.post('/api/recipes', json=data)
    assert response.status_code == 200
    assert response.get_json()['description'] is None

    # test tags validation:
    data['tags'].append(9999)
    response = client.post('/api/recipes', json=data)
    assert response.status_code == 400
    data['tags'].remove(9999)
    
    # test meal types validation
    data['meal_type_id'] = 9999
    response = client.post('/api/recipes', json=data)
    assert response.status_code == 400


def test_edit_recipe(client: FlaskClient, app, testing_setup):
    recipe = testing_setup['recipes']["published"][0]

    # logged out request:
    new_name = "New Meal Name"
    response = client.put(f'/api/recipes/{recipe.id}', json={
        "name": new_name,
    })
    assert response.status_code == 401

    # wrong user request
    user = testing_setup['users']['active'][1]
    assert user.id != recipe.author_id
    with app.test_request_context():
        login_user(user)

    response = client.put(f'/api/recipes/{recipe.id}', json={
        "name": new_name,
    })
    assert response.status_code == 403

    # correct user request
    with app.test_request_context():
        login_user(recipe.author)
    response = client.put(f'/api/recipes/{recipe.id}', json={
        "name": new_name,
    })
    assert response.status_code == 200
    assert response.get_json()['name'] == new_name

    # superuser request
    superuser = testing_setup['users']['super'][0]
    with app.test_request_context():
        login_user(superuser)

    new_name = "Super meal"
    response = client.put(f'/api/recipes/{recipe.id}', json={
        "name": new_name,
    })
    assert response.status_code == 200
    assert response.get_json()['name'] == new_name


def test_get_recipe(client: FlaskClient, app, testing_setup):
    # personal recipe
    recipe = testing_setup['recipes']['personal'][0]

    # non-logged in request
    response = client.get(f'/api/recipes/{recipe.id}')
    assert response.status_code == 404

    # wrong user
    user = testing_setup['users']['active'][1]
    assert user.id != recipe.author_id
    with app.test_request_context():
        login_user(user)

    response = client.get(f'/api/recipes/{recipe.id}')
    assert response.status_code == 404

    # logged in request
    with app.test_request_context():
        login_user(recipe.author)

    response = client.get(f'/api/recipes/{recipe.id}')
    assert response.status_code == 200
    assert response.get_json()['name'] == recipe.name

    # request with `recipe.is_visible` set to False
    recipe.is_visible = False
    recipe.query.session.commit()

    response = client.get(f'/api/recipes/{recipe.id}')
    assert response.status_code == 404

    # super user
    user = testing_setup['users']['super'][0]
    assert user.id != recipe.author_id
    with app.test_request_context():
        login_user(user)
    response = client.get(f'/api/recipes/{recipe.id}')
    assert response.status_code == 200
    assert response.get_json()['name'] == recipe.name

    # published requests
    recipe = testing_setup['recipes']['published'][0]
    with app.test_request_context():
        logout_user()

    response = client.get(f'/api/recipes/{recipe.id}')
    assert response.status_code == 200
    assert response.get_json()['name'] == recipe.name


def test_get_recipe_list(client: FlaskClient, app, testing_setup):
    response = client.get('/api/recipes')
    assert response.status_code == 200
    assert response.get_json()["total"] == len(
        testing_setup['recipes']['published'])

    # logged in user
    user = testing_setup['users']['active'][0]
    with app.test_request_context():
        login_user(user)

    response = client.get('/api/recipes')
    assert response.status_code == 200
    
    total_objects = Recipe.query.filter(
        or_(
            and_(
                Recipe.is_visible.is_(True),
                Recipe.is_published.is_(True)
            ),
            and_(
                Recipe.author_id == user.id,
                Recipe.is_visible.is_(True),
            )
        )
    )

    assert response.get_json()["total"] == total_objects.count()
    
    # superuser
    user = testing_setup['users']['super'][0]
    with app.test_request_context():
        login_user(user)

    response = client.get('/api/recipes')
    assert response.status_code == 200
    assert response.get_json()["total"] == Recipe.query.count()


def test_delete_recipe(client: FlaskClient, app, testing_setup):
    recipe = testing_setup['recipes']["published"][0]
    
    # non-logged in:
    response = client.delete(f'/api/recipes/{recipe.id}')
    assert response.status_code == 401
    
    # wrong user:
    user = testing_setup['users']['active'][1]
    assert user.id != recipe.author_id
    with app.test_request_context():
        login_user(user)

    response = client.delete(f'/api/recipes/{recipe.id}')
    assert response.status_code == 403

    # correct user:
    with app.test_request_context():
        login_user(recipe.author)

    response = client.delete(f'/api/recipes/{recipe.id}')
    assert response.status_code == 204
    response = client.get(f'/api/recipes/{recipe.id}')
    assert response.status_code == 404

    # un-delete the recipe
    recipe.is_visible = True
    Recipe.query.session.commit()
    
    # delete as a superuser
    user = testing_setup['users']['super'][0]
    with app.test_request_context():
        login_user(user)

    response = client.delete(f'/api/recipes/{recipe.id}')
    assert response.status_code == 204
    response = client.get(f'/api/recipes/{recipe.id}')
    assert response.status_code == 200
    
    with app.test_request_context():
        logout_user()
    response = client.get(f'/api/recipes/{recipe.id}')
    assert response.status_code == 404
