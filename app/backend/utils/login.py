from functools import wraps
from flask import abort
from flask_login import current_user, login_required

from backend.users.models import User


def superuser_only(func):
    """An extension of the `flask_login.login_required` function that
    checks if the user is a superuser, and aborts with `403` if not."""
    @wraps(func)
    @login_required
    def decorated_view(*args, **kwargs):
        if not current_user.is_superuser:
            abort(403)
        return func(*args, **kwargs)
    return decorated_view


def is_user_or_superuser(user: User):        
    return ((current_user == user) or current_user.is_superuser)
