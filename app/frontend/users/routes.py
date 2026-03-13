from flask import Blueprint, render_template
from flask_login import login_required

from backend.users.models import ProfilePicture, User


users_front_bp = Blueprint(
    name='users_frontend',
    import_name=__name__,
    template_folder='templates')


@users_front_bp.route('/signup', methods=['GET'])
def signup_page(): 
    return render_template('/users/auth/register_page.html')


@users_front_bp.route('/signin', methods=['GET'])
def login_page(): 
    return render_template('/users/auth/login_page.html')


@users_front_bp.route('/logout', methods=['GET'])
@login_required
def logout_page(): 
    return render_template('/users/auth/logout_page.html')


@users_front_bp.route('/users/<int:id>', methods=['GET'])
def user_profile_page(id: int):
    user = User.query.filter(User.id == id).first_or_404()
    return render_template('/users/profile_page.html')


@users_front_bp.route('/users/<int:id>/edit', methods=['GET'])
@login_required
def user_profile_edit_page(id: int):
    context = {
        'pfp_list': ProfilePicture.query.all()
    }
    return render_template('/users/profile_page_edit.html', context=context)