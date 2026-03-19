from flask.testing import FlaskClient
from backend.recipes.cli import create_meal_type, delete_meal_type
from backend.recipes.models import MealType


def test_get_meal_type(client: FlaskClient):
    meal_type: MealType = MealType.query.first()

    response = client.get(f'/api/meal-types/{meal_type.id}')
    
    assert response.status_code == 200
    assert response.get_json()['name'] == meal_type.name
    
    unexistent_id = 9999
    assert MealType.query.filter_by(id=unexistent_id).first() is None
    
    response = client.get(f'/api/meal-types/{unexistent_id}')
    assert response.status_code == 404


def test_get_meal_type_list(client: FlaskClient):
    meal_types = MealType.query.all()
    
    response = client.get('/api/meal-types')
    assert response.status_code == 200
    assert response.get_json()["total"] == len(meal_types)


def test_create_meal_type(runner):
    name = 'Test Meal'
    result = runner.invoke(
        create_meal_type,
        args=[name]
    )
    assert result.exit_code == 0
    
    meal_type = MealType.query.filter_by(name=name).first()
    
    assert meal_type is not None
    assert meal_type.name == name
    

def test_delete_meal_type(runner):
    all_meal_types = MealType.query.all()
    
    meal_type: MealType = all_meal_types[0]

    result = runner.invoke(
        delete_meal_type,
        args=[str(meal_type.id)]
    )
    
    assert result.exit_code == 0
    assert MealType.query.filter_by(id=meal_type.id).first() is None
    
    # delete all
    result = runner.invoke(
        delete_meal_type,
        args=["all"]
    )
    assert result.exit_code == 0
    assert len(MealType.query.all()) == 0
    