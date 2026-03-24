from flask import redirect, url_for
from flask_admin.contrib.sqla import ModelView
from flask_admin import AdminIndexView
from flask_login import current_user


class ProtectedModelView(ModelView):
    def is_accessible(self):
        return current_user.is_superuser
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('users_frontend.login_page'))
    
    
class AdminHomeView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_superuser
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('users_frontend.login_page'))