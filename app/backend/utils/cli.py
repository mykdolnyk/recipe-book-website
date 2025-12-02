import click
import json
import config
from app_factory import db
from flask.cli import with_appcontext
from backend.recipes.models import MealType


@click.command("loadfixtures")
@with_appcontext
def load_fixtures():
    total_entries_pasted = 0
    total_entries_skipped = 0

    with open(config.FIXTURES_DIR / 'mealtypes.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    for entry in data:
        meal_type = MealType(**entry)
        if MealType.query.filter(MealType.id == meal_type.id).first():
            total_entries_skipped += 1
        else:
            db.session.add(meal_type)
            total_entries_pasted += 1

    db.session.commit()

    click.echo('The fixtures have been created successully.' +
               f'\nTotal entries pasted: {total_entries_pasted}.' +
               f'\nTotal entries skipped: {total_entries_skipped}.')
