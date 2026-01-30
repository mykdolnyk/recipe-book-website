import random
from flask_login import current_user, login_user, logout_user
from logging import getLogger
from flask.blueprints import Blueprint
from pydantic import ValidationError
from backend.utils.pagination import paginate
from backend.utils.misc import ObjectManager, safe_commit
from backend.utils.login import is_owner_or_superuser
from backend.users.schemas import UserCreate, UserDetailedSchema, UserUpdate, UserLogin, UserSchema
from backend.users.models import ProfilePicture, User
from backend.utils.errors import create_error_response, ErrorCode
from flask import abort, jsonify, request
from app_factory import db


logger = getLogger(__name__)


user_bp = Blueprint(
    name='users',
    import_name=__name__,
    url_prefix='/api'
)


@user_bp.route('/users', methods=['GET'])
def get_user_list():
    if current_user.is_superuser:
        query = User.query
    else:
        query = User.active()

    pagination = paginate(
        request_args=request.args,
        sqlalchemy_query=query,
        pydantic_model=UserSchema,
        list_name='user_list',
    )

    return jsonify(pagination)


@user_bp.route('/users', methods=["POST"])
def register_user():    
    manager = ObjectManager(
        db_model=User,
        create_schema=UserCreate,
        get_schema=UserSchema
    )
    manager.create_object(
        request.get_json(),
        exclude_for_db=['password_confirm'],
        commit=False
    )
    with db.session.no_autoflush:
        pfp_ids = [pfp.id for pfp in ProfilePicture.query.all()]
    
    if manager.success:
        manager.object.profile_picture_id = random.choice(pfp_ids)
        manager.commit_changes()

    response = manager.generate_response()
    return response


@user_bp.route('/users/<int:id>', methods=["GET"])
def get_user_info(id: int):
    user = User.active().filter_by(id=id).first()

    if not user:
        return create_error_response(ErrorCode.USER_NOT_FOUND)

    response = UserDetailedSchema.model_validate(user).model_dump()
    return jsonify(response)


@user_bp.route('/users/<int:id>', methods=["PUT"])
def edit_user(id: int):
    user: User = User.active().filter_by(id=id).first()
    if not user:
        return create_error_response(ErrorCode.USER_NOT_FOUND, status_code=404)

    if not is_owner_or_superuser(user):
        abort(403)

    manager = ObjectManager(
        db_model=User,
        update_schema=UserUpdate,
        get_schema=UserDetailedSchema,
    )
    manager.update_object(
        obj=user,
        data=request.get_json()
    )

    response = manager.generate_response()
    return response


@user_bp.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id: int):
    args = request.args
    if args.get('confirm', 'false').lower() != 'true':
        return create_error_response('Deletion was not confirmed.', status_code=403)

    user: User = User.active().filter_by(id=id).first()

    if not user:
        return create_error_response(ErrorCode.USER_NOT_FOUND)

    if not is_owner_or_superuser(user):
        abort(403)

    user.is_active = False
    errors = safe_commit(db.session)
    if errors:
        return errors

    return '', 204


@user_bp.route('/auth/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return create_error_response('Already logged in.', status_code=400)

    try:
        login_schema = UserLogin(**request.get_json())
    except ValidationError as error:
        return create_error_response(error)
    user: User = login_schema.user

    login_user(user)

    response = {
        'id': user.id
    }

    return jsonify(response)


@user_bp.route('/auth/logout', methods=['POST'])
def logout():
    if not current_user.is_authenticated:
        return create_error_response('Already logged out.', status_code=200)

    logout_user()

    return '', 200
