import flask_login


class AnonymousUser(flask_login.AnonymousUserMixin):
    id = None
    is_superuser = False