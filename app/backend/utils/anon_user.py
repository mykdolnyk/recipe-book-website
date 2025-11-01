import flask_login


class AnonymousUser(flask_login.AnonymousUserMixin):
    is_superuser = False