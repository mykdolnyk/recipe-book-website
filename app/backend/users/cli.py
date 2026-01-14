import bcrypt
import click
from pydantic import ValidationError
from sqlalchemy import func
from backend.users.helpers import create_user_instance
from backend.users.models import User
from backend.users.routes import user_bp
from app_factory import db
from backend.users.schemas import UserCreate


user_bp.cli.help = 'Perform User-related operations.'


@user_bp.cli.command('createsuperuser', help='Create a Super user.')
@click.argument('email')
@click.argument('name')
@click.password_option()
def create_superuser(name: str, email: str, password: str):
    if User.query.filter(func.lower(User.email) == email.lower()).first():
        raise click.ClickException('The email is already taken.')
    
    try:
        schema = UserCreate(
                name=name,
                email=email,
                password=password,
                password_confirm=password,
            )
    except ValidationError as err:
        raise click.ClickException(err)
    
    
    user = create_user_instance(user_schema=schema)
    user.is_superuser = True

    db.session.add(user)
    db.session.commit()

    click.echo('The superuser has been successfully created.')
    return
