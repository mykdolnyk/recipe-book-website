import click
from backend.utils.fixtures import load_fixtures
from flask.cli import with_appcontext


@click.command("loadfixtures")
@with_appcontext
def load_fixtures_command():
    result = load_fixtures()

    click.echo('The fixtures have been created successully.' +
               f'\nTotal entries pasted: {result['total_entries_pasted']}.' +
               f'\nTotal entries skipped: {result['total_entries_skipped']}.')