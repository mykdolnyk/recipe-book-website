import json
import random
from flask_login import current_user, login_user, logout_user
from logging import getLogger
from flask.blueprints import Blueprint
from pydantic import ValidationError
from backend.utils.pagination import paginate
from backend.utils.misc import ObjectManager, safe_commit
from backend.utils.login import is_owner_or_superuser
from backend.utils.attempt_restriction import AttemptRestricter
from backend.users.schemas import UserCreate, UserDetailedSchema, UserUpdate, UserLogin, UserSchema
from backend.users.models import ProfilePicture, User
from backend.utils.errors import create_error_response, ErrorCode
from flask import abort, jsonify, make_response, request, session
from app_factory import db, redis_client
import config

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


@user_bp.route('/users/<int:id>', methods=["GET"])
def get_user_info(id: int):
    user = User.active().filter_by(id=id).first()
    if not user:
        return create_error_response(ErrorCode.USER_NOT_FOUND)

    cache_key = f'user-data:id={user.id}'
    response = redis_client.get(cache_key)

    if response is not None:
        response = json.loads(response)
    else:
        response = UserDetailedSchema.model_validate(user).model_dump()
        redis_client.set(cache_key, json.dumps(response), 600)

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
    
    redis_client.delete(f'user-data:id={user.id}')

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
        if len(pfp_ids) != 0:
            manager.object.profile_picture_id = random.choice(pfp_ids)
        manager.commit_changes()

    response = manager.generate_response()
    return response


@user_bp.route('/auth/login', methods=['POST'])
def login():
    if current_user.is_authenticated:
        return create_error_response('Already logged in.', status_code=400)

    restricter = AttemptRestricter(key_prefix='login',
                                   max_attempts=config.LOGIN_ATTEMPTS_MAX,
                                   timeout=config.LOGIN_RESTRICTION_TIMEOUT)
    if restricter.is_restricted():
        return create_error_response(ErrorCode.TOO_MANY_LOGIN_ATTEMPTS)

    try:
        login_schema = UserLogin(**request.get_json())
    except ValidationError as error:
        restricter.increase_attempt_count()
        restricter.add_restriction_if_needed()
        
        return create_error_response(error)
    
    user: User = login_schema.user
    login_user(user)

    response = jsonify({
        'id': user.id
    })
    response.delete_cookie("csrf_token")
    session.pop("csrf_token")
    
    return response

@user_bp.route('/auth/logout', methods=['POST'])
def logout():
    if not current_user.is_authenticated:
        return create_error_response('Already logged out.', status_code=200)

    logout_user()
    
    response = jsonify({
        'msg': "Successfully logged out."
    })
    response.delete_cookie("csrf_token")
    session.pop("csrf_token")

    return response