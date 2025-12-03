import click
from sqlalchemy import delete, func
from backend.recipes.models import MealType
from backend.recipes.routes import recipes_bp
from backend.utils.misc import slugify
from app_factory import db


recipes_bp.cli.help = 'Perform Recipe-related operations.'


@recipes_bp.cli.command('createrecipetype', help='Create a Meal Type.')
@click.argument('name')
def create_meal_type(name: str):
    if MealType.query.filter(func.lower(MealType.name) == name.lower()).first():
        click.echo('Meal Type with such name already exists.')
        return False

    meal_type = MealType(
        name=name.title(),
        slug=slugify(name),
    )
    db.session.add(meal_type)
    db.session.commit()

    click.echo('The Meal Type has been successfully created.')
    return True


@recipes_bp.cli.command('deleterecipetype', help='Delete a Meal Type.')
@click.argument('id')
def delete_meal_type(id: int):
    if id == "all":
        # Delete all
        db.session.execute(delete(MealType))
        db.session.commit()
        click.echo('All Meal Types have been successfully deleted.')
        return True
    
    meal_type = MealType.query.filter_by(id=id).first()
    if not meal_type:
        click.ClickException('Meal Type with such ID doesn\'t exist.')

    db.session.delete(meal_type)
    db.session.commit()

    click.echo('The Meal Type has been successfully deleted.')
    return True