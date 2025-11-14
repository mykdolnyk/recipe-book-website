import click
from sqlalchemy import delete, func
from backend.recipes.models import PeriodType
from backend.recipes.routes import recipes_bp
from backend.utils.misc import slugify
from app_factory import db


recipes_bp.cli.help = 'Perform Recipe-related operations.'


@recipes_bp.cli.command('createrecipetype', help='Create a Recipe Type.')
@click.argument('name')
def create_recipe_type(name: str):
    if PeriodType.query.filter(func.lower(PeriodType.name) == name.lower()).first():
        click.echo('Recipe Type with such name already exists.')
        return False

    recipe_type = PeriodType(
        name=name.title(),
        slug=slugify(name),
    )
    db.session.add(recipe_type)
    db.session.commit()

    click.echo('The Recipe Type has been successfully created.')
    return True


@recipes_bp.cli.command('deleterecipetype', help='Delete a Recipe Type.')
@click.argument('id')
def create_recipe_type(id: int):
    if id == "all":
        # Delete all
        db.session.execute(delete(PeriodType))
        db.session.commit()
        click.echo('All Recipe Types have been successfully deleted.')
        return True
    
    recipe_type = PeriodType.query.get(id)
    if not recipe_type:
        click.echo('Recipe Type with such ID doesn\'t exist.')
        return False

    db.session.delete(recipe_type)
    db.session.commit()

    click.echo('The Recipe Type has been successfully deleted.')
    return True