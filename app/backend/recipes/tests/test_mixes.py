from flask.testing import FlaskClient
from flask_login import login_user
from app_factory import db
from backend.recipes.models import RecipeMix
from backend.users.models import User


def test_create_recipe_mix(client: FlaskClient, app, testing_setup):
    # Set everything up
    recipe_tag_1 = testing_setup['recipe_tags'][0]
    recipe_tag_2 = testing_setup['recipe_tags'][1]
    
    recipes_with_tag_1 = testing_setup['recipes']['published'][0:2]
    recipes_with_tag_2 = testing_setup['recipes']['published'][2:4]
    recipes_with_tag_1_and_2 = testing_setup['recipes']['published'][4:6]
    recipes_with_no_tag = testing_setup['recipes']['published'][6:]

    for recipe in recipes_with_tag_1:
        recipe.tags = [recipe_tag_1]
        
    for recipe in recipes_with_tag_2:
        recipe.tags = [recipe_tag_2]
        
    for recipe in recipes_with_tag_1_and_2:
        recipe.tags = [recipe_tag_1, recipe_tag_2]
        
    for recipe in recipes_with_no_tag:
        recipe.tags = []
        
    db.session.commit()
    
    # ----- Testing starts -----
    
    # Query with no specifications
    post_body = {}
    response = client.post('/api/recipe-mixes', json=post_body)
    assert response.status_code == 400
    
    # Query with meal types
    post_body = {
        "meal_type_ids": [1, 2, 3, 4]
    }
    response = client.post('/api/recipe-mixes', json=post_body)
    assert response.status_code == 200
    assert len(response.get_json()['recipes']) == 4
    
    # Query with unexistent meal type
    post_body = {
        "meal_type_ids": [1, 2, 3333, 4]
    }
    response = client.post('/api/recipe-mixes', json=post_body)
    assert response.status_code == 200
    assert len(response.get_json()['recipes']) == 3 # It ignores unexistent categories
    
    # --- Test Calories ---
    
    # Set Up
    for recipe in testing_setup['recipes']['published']:
        recipe.calories = 75
        
    correct_min_recipe = testing_setup['recipes']['published'][0]
    correct_min_recipe.calories = 200
    
    correct_max_recipe = testing_setup['recipes']['published'][1]
    correct_max_recipe.calories = 50
    db.session.commit()
    
    # Test Min
    post_body = {
        "meal_type_ids": [1, 2, 3, 4],
        "min_calories": 100
    }
    response = client.post('/api/recipe-mixes', json=post_body)
    
    assert response.status_code == 200
    assert len(response.get_json()['recipes']) == 1 # It ignores recipes that do not fit the criteria
    assert response.get_json()['recipes'][0]['id'] == correct_min_recipe.id
    
    # Test Max
    post_body = {
        "meal_type_ids": [1, 2, 3, 4],
        "max_calories": 50
    }
    response = client.post('/api/recipe-mixes', json=post_body)
    
    assert response.status_code == 200
    assert len(response.get_json()['recipes']) == 1
    assert response.get_json()['recipes'][0]['id'] == correct_max_recipe.id
    
    # --- Test Include Tags ---
    # Tag 1
    post_body = {
        "meal_type_ids": [1, 2, 3, 4],
        "include_tags": [1]
    }
    response = client.post('/api/recipe-mixes', json=post_body)
    
    assert response.status_code == 200
    for recipe in response.get_json()['recipes']:
        has_tag_1 = False
        for tag in recipe['tags']:
            if tag['id'] == 1: has_tag_1 = True
            
        assert has_tag_1
    
    # Tag 2
    post_body = {
        "meal_type_ids": [1, 2, 3, 4],
        "include_tags": [2]
    }
    response = client.post('/api/recipe-mixes', json=post_body)
    
    assert response.status_code == 200
    for recipe in response.get_json()['recipes']:
        has_tag_2 = False
        for tag in recipe['tags']:
            if tag['id'] == 2: has_tag_2 = True
            
        assert has_tag_2
        
    # Tag 1 and 2
    post_body = {
        "meal_type_ids": [1, 2, 3, 4],
        "include_tags": [1, 2]
    }
    response = client.post('/api/recipe-mixes', json=post_body)
    
    assert response.status_code == 200
    for recipe in response.get_json()['recipes']:
        has_tag_1 = False
        has_tag_2 = False
        
        for tag in recipe['tags']:
            if tag['id'] == 1: has_tag_1 = True
            if tag['id'] == 2: has_tag_2 = True
            
        assert has_tag_1 or has_tag_2
        
    # --- Test Exclude Tags ---
    
    # Tag 1
    post_body = {
        "meal_type_ids": [1, 2, 3, 4],
        "exclude_tags": [1]
    }
    response = client.post('/api/recipe-mixes', json=post_body)
    
    assert response.status_code == 200
    for recipe in response.get_json()['recipes']:
        has_tag_1 = False
        for tag in recipe['tags']:
            if tag['id'] == 1: has_tag_1 = True
            
        assert not has_tag_1
    
    # Tag 2
    post_body = {
        "meal_type_ids": [1, 2, 3, 4],
        "exclude_tags": [2]
    }
    response = client.post('/api/recipe-mixes', json=post_body)
    
    assert response.status_code == 200
    for recipe in response.get_json()['recipes']:
        has_tag_2 = False
        for tag in recipe['tags']:
            if tag['id'] == 2: has_tag_2 = True
            
        assert not has_tag_2
        
    # Tag 1 and 2
    post_body = {
        "meal_type_ids": [1, 2, 3, 4],
        "exclude_tags": [1, 2]
    }
    response = client.post('/api/recipe-mixes', json=post_body)
    
    assert response.status_code == 200
    for recipe in response.get_json()['recipes']:
        has_tag_1 = False
        has_tag_2 = False
        
        for tag in recipe['tags']:
            if tag['id'] == 1: has_tag_1 = True
            if tag['id'] == 2: has_tag_2 = True
            
        assert (not has_tag_1) and (not has_tag_2)
    
    # --- Test Default Visibility ---
    
    personal_recipe = testing_setup['recipes']['personal'][0]
    
    # Narrow the criteria
    personal_recipe.calories = 9999
    db.session.commit()
    
    post_body = {
        "meal_type_ids": [1, 2, 3, 4, 5],
        "min_calories": 9999
    }
    
    # Test
    response = client.post('/api/recipe-mixes', json=post_body)
    assert response.status_code == 200
    assert len(response.get_json()['recipes']) == 0

    # Login
    with app.test_request_context():
        login_user(personal_recipe.author)
    
    # Test
    response = client.post('/api/recipe-mixes', json=post_body)
    assert response.status_code == 200
    assert len(response.get_json()['recipes']) == 1
    assert response.get_json()['recipes'][0]['id'] == personal_recipe.id
        
    # --- Test Public Only ---
    post_body = {
        "meal_type_ids": [1, 2, 3, 4, 5],
        "min_calories": 9999,
        "public_only": True
    }
    response = client.post('/api/recipe-mixes', json=post_body)
    assert response.status_code == 200
    assert len(response.get_json()['recipes']) == 0
    
    post_body = {
        "meal_type_ids": [1, 2, 3, 4, 5],
        "public_only": True
    }
    response = client.post('/api/recipe-mixes', json=post_body)
    assert response.status_code == 200
    assert len(response.get_json()['recipes']) != 0
    
    # --- Test Personal Only ---
    post_body = {
        "meal_type_ids": [1, 2, 3, 4, 5],
        "personal_only": True
    }
    response = client.post('/api/recipe-mixes', json=post_body)
    assert response.status_code == 200
    
    for recipe in response.get_json()['recipes']:
        assert recipe['author']['id'] == personal_recipe.author.id


def test_get_recipe_mix(client: FlaskClient, app, testing_setup):
    recipe_mix: RecipeMix = testing_setup['recipe_mixes'][0]

    # non-logged in request
    response = client.get(f'/api/recipe-mixes/{recipe_mix.id}')
    assert response.status_code == 404

    # wrong user
    user = testing_setup['users']['active'][1]
    assert user.id != recipe_mix.author_id
    with app.test_request_context():
        login_user(user)

    response = client.get(f'/api/recipe-mixes/{recipe_mix.id}')
    assert response.status_code == 404

    # logged in request
    with app.test_request_context():
        login_user(recipe_mix.author)

    response = client.get(f'/api/recipe-mixes/{recipe_mix.id}')
    assert response.status_code == 200
    assert response.get_json()['name'] == recipe_mix.name

    # super user
    user = testing_setup['users']['super'][0]
    assert user.id != recipe_mix.author_id
    with app.test_request_context():
        login_user(user)
    response = client.get(f'/api/recipe-mixes/{recipe_mix.id}')
    assert response.status_code == 200
    assert response.get_json()['name'] == recipe_mix.name


def test_get_recipe_list(client: FlaskClient, app, testing_setup):
    # non logged-in
    response = client.get('/api/recipe-mixes')
    assert response.status_code == 200
    assert response.get_json()["total"] == 0

    # logged in user
    user: User = testing_setup['users']['active'][0]
    with app.test_request_context():
        login_user(user)

    response = client.get('/api/recipe-mixes')
    assert response.status_code == 200
    assert response.get_json()["total"] == len(user.mixes) != 0
    
    # superuser
    user = testing_setup['users']['super'][0]
    with app.test_request_context():
        login_user(user)

    response = client.get('/api/recipe-mixes')
    assert response.status_code == 200
    assert response.get_json()["total"] == len(testing_setup['recipe_mixes'])


def test_edit_recipe_mix(client: FlaskClient, app, testing_setup):
    recipe_mix: RecipeMix = testing_setup['recipe_mixes'][0]

    # logged out request:
    new_name = "New Recipe Mix Name"
    response = client.put(f'/api/recipe-mixes/{recipe_mix.id}', json={
        "name": new_name,
    })
    assert response.status_code == 404

    # wrong user request
    user = testing_setup['users']['active'][1]
    assert user.id != recipe_mix.author_id
    with app.test_request_context():
        login_user(user)

    response = client.put(f'/api/recipe-mixes/{recipe_mix.id}', json={
        "name": new_name,
    })
    assert response.status_code == 404

    # correct user request
    with app.test_request_context():
        login_user(recipe_mix.author)
    response = client.put(f'/api/recipe-mixes/{recipe_mix.id}', json={
        "name": new_name,
    })
    assert response.status_code == 200
    assert response.get_json()['name'] == new_name

    # superuser request
    superuser = testing_setup['users']['super'][0]
    with app.test_request_context():
        login_user(superuser)

    new_name = "Super meal"
    response = client.put(f'/api/recipe-mixes/{recipe_mix.id}', json={
        "name": new_name,
    })
    assert response.status_code == 200
    assert response.get_json()['name'] == new_name


def test_delete_recipe_mix(client: FlaskClient, app, testing_setup):
    recipe_mix: RecipeMix = testing_setup['recipe_mixes'][0]

    # non-logged in:
    response = client.delete(f'/api/recipe-mixes/{recipe_mix.id}')
    assert response.status_code == 404
    
    # wrong user:
    user = testing_setup['users']['active'][1]
    assert user.id != recipe_mix.author_id
    with app.test_request_context():
        login_user(user)

    response = client.delete(f'/api/recipe-mixes/{recipe_mix.id}')
    assert response.status_code == 404

    # correct user:
    with app.test_request_context():
        login_user(recipe_mix.author)

    response = client.get(f'/api/recipe-mixes/{recipe_mix.id}')
    assert response.status_code == 200
    response = client.delete(f'/api/recipe-mixes/{recipe_mix.id}')
    assert response.status_code == 204
    response = client.get(f'/api/recipe-mixes/{recipe_mix.id}')
    assert response.status_code == 404

    # get a new recipe mix as previous one was deleted
    recipe_mix: RecipeMix = testing_setup['recipe_mixes'][1]
    
    # delete as a superuser
    user = testing_setup['users']['super'][0]
    with app.test_request_context():
        login_user(user)

    response = client.get(f'/api/recipe-mixes/{recipe_mix.id}')
    assert response.status_code == 200
    response = client.delete(f'/api/recipe-mixes/{recipe_mix.id}')
    assert response.status_code == 204
    response = client.get(f'/api/recipe-mixes/{recipe_mix.id}')
    assert response.status_code == 404
