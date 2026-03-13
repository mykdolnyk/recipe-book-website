from functools import wraps
from typing import TYPE_CHECKING
from flask import abort, redirect, url_for
from flask_login import current_user
from types import SimpleNamespace

if TYPE_CHECKING:
    from backend.users.models import User


def superuser_only(func):
    """A decorator function that checks if the user is logged in 
    and is a superuser, aborts if not."""
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if current_user.is_anonymous:
            abort(401)
        if not current_user.is_superuser:
            abort(403)
        return func(*args, **kwargs)
    return decorated_view


def is_owner_or_superuser(user: 'User'):        
    return (current_user.is_authenticated and ((current_user.id == user.id) or current_user.is_superuser))


def redirect_to_login_callback():
    """A callback function for `login_manager.unauthorized_handler` that
    redirects users to the login page"""
    return redirect(url_for('users_frontend.login_page'))


def authorization_context_processors():
    def is_owner_or_superuser_id(id: int):
        return is_owner_or_superuser(SimpleNamespace(id=id)) # an object that has .id field

    return {
        'is_owner_or_superuser_id': is_owner_or_superuser_id
    }
