from app_factory import db
from flask.testing import FlaskClient
from flask_login import login_user, logout_user
from sqlalchemy import and_, or_

from backend.recipes.models import MealType, Recipe, RecipeTag


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
    assert response.status_code == 302

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
    assert response.get_json()["total"] == Recipe.published().count()


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


def test_recipe_search(client: FlaskClient, app, testing_setup):
    # With no params
    response = client.get(f'/api/recipes/search')
    assert response.status_code == 200
    assert response.get_json()["total"] == len(
        testing_setup['recipes']['published'])

    # === Test Name ===
    recipe: Recipe = testing_setup['recipes']['published'][-1]
    recipe.name = 'Fancy Pasta'

    response = client.get(f'/api/recipes/search?text=fancy')
    assert response.status_code == 200
    assert response.get_json()["total"] == 1

    # === Test Ingredients ===
    recipe: Recipe = testing_setup['recipes']['published'][-2]
    recipe.ingredients = 'Chicken Nugget'

    response = client.get('/api/recipes/search?text=nugget')
    assert response.status_code == 200
    assert response.get_json()["total"] == 1

    # Multiple incomplete words
    response = client.get('/api/recipes/search?text=nug chick')
    assert response.status_code == 200
    assert response.get_json()["total"] == 1

    # === Test Description ===
    recipe: Recipe = testing_setup['recipes']['published'][-3]
    recipe.description = 'Delicious Dumplings just for you!'

    response = client.get('/api/recipes/search?text=just for you')
    assert response.status_code == 200
    assert response.get_json()["total"] == 1

    # === Test Scoring ===
    name_recipe: Recipe = testing_setup['recipes']['published'][0]
    name_recipe.name = 'Recipe Search Testing Name'

    description_recipe: Recipe = testing_setup['recipes']['published'][1]
    description_recipe.description = 'Recipe Search Testing Description'

    ingredients_recipe: Recipe = testing_setup['recipes']['published'][2]
    ingredients_recipe.ingredients = 'Recipe Search Testing Ingredients'

    full_name_recipe: Recipe = testing_setup['recipes']['published'][3]
    full_name_recipe.name = 'Recipe Testing Search Name (full name match)'

    search_query = "Testing Search"

    response = client.get(f'/api/recipes/search?text={search_query}')
    assert response.status_code == 200
    results = response.get_json()["recipe_list"]
    assert len(results) == 4
    assert results[0]['id'] == full_name_recipe.id
    assert results[1]['id'] == name_recipe.id
    assert results[2]['id'] == ingredients_recipe.id
    assert results[3]['id'] == description_recipe.id

    # === Test No Matches ===
    response = client.get(
        '/api/recipes/search?text=textthatisnotpresentanywhere')
    assert response.status_code == 200
    assert response.get_json()["total"] == 0

    # === Test Tags ===
    tag: RecipeTag = testing_setup['recipe_tags'][0]
    recipe_with_tag: Recipe = testing_setup['recipes']['published'][0]
    recipe_with_tag.tags.append(tag)

    response = client.get(f'/api/recipes/search?recipe-tags={tag.id}')
    assert response.status_code == 200
    assert response.get_json()["total"] == len(tag.recipes) != 0

    # === Test Meal Types ===
    meal_type: MealType = testing_setup['meal_types'][0]
    response = client.get(f'/api/recipes/search?meal-types={meal_type.id}')
    assert response.status_code == 200
    assert response.get_json()["total"] == Recipe.published().filter(
        Recipe.meal_type_id == meal_type.id
    ).count() != 0

    # Multiple meal types
    additional_meal_type: MealType = testing_setup['meal_types'][1]
    response = client.get(
        f'/api/recipes/search?meal-types={meal_type.id}&meal-types={additional_meal_type.id}')
    assert response.status_code == 200
    assert response.get_json()["total"] == Recipe.published().filter(
        or_(
            Recipe.meal_type_id == meal_type.id,
            Recipe.meal_type_id == additional_meal_type.id
        )
    ).count() != 0

    # === Test Combining All ===
    tag = testing_setup['recipe_tags'][0]
    meal_type = testing_setup['meal_types'][0]
    
    for idx, recipe in enumerate(testing_setup['recipes']['published'][:10]):
        # every 2nd recipe has "fancy" in name
        if idx % 2 == 0:
            recipe.name = f'fAnCy recipe {idx}'
        
        # every 4th recipe has the corresponding meal type
        if idx % 4 == 0:
            recipe.meal_type_id = meal_type.id
        
        # 2 recipes every 8 recipes idk
        if idx % 8 < 2:
            recipe.tags.append(tag)
        
    # for 10 recipes there would be only 2 recipes matchin all 3 criteria
    db.session.commit()
    
    response = client.get(
        f'/api/recipes/search?text=fancy&recipe-tags={tag.id}&meal-types={meal_type.id}')
    assert response.status_code == 200
    assert response.get_json()["total"] == 2


def test_popular_recipes(client: FlaskClient, app, testing_setup):
    # Clean setup with no likes
    response = client.get('/api/recipes/popular')
    assert response.status_code == 200
    assert len(response.get_json()) == 0
    
    # Like some recipes
    
    with app.test_request_context():
        login_user(testing_setup['users']['active'][0])
    
    liked_recipes = set()
    for i in range(0, len(testing_setup['recipes']['published']), 3):
        recipe = testing_setup['recipes']['published'][i]
        liked_recipes.add(recipe)

        response = client.post(f'/api/recipes/{recipe.id}/like')
        assert response.status_code == 201
    
    # Check again
    response = client.get('/api/recipes/popular')
    assert response.status_code == 200
    assert len(response.get_json()) == len(liked_recipes)
    
    # Like more 
    for i in range(1, len(testing_setup['recipes']['published']), 3):
        recipe = testing_setup['recipes']['published'][i]
        liked_recipes.add(recipe)

        response = client.post(f'/api/recipes/{recipe.id}/like')
        assert response.status_code == 201
    
    # Check again
    response = client.get('/api/recipes/popular')
    assert response.status_code == 200
    assert len(response.get_json()) == len(liked_recipes)
    