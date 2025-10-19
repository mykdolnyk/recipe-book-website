from flask.blueprints import Blueprint
from pydantic import ValidationError
from backend.users.helpers import create_user_instance
from backend.users.schemas import UserCreateSchema, UserEditSchema
from backend.users.models import User
from backend.utils.errors import create_error_response, ErrorCode
from flask import jsonify, request
from app_factory import db


user_bp = Blueprint(
    name='users',
    import_name=__name__,
    url_prefix='/api'
)


@user_bp.route('/users', methods=['GET'])
def get_user_list():
    page = request.args.get('page', 1)
    per_page = request.args.get('per-page', 5)

    pagination = User.query.paginate(page=page,
                                     per_page=per_page,
                                     max_per_page=25,
                                     error_out=False)
    
    user_list = [user.info_dict() for user in pagination.items]

    return jsonify({
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "user_list": user_list
    })


@user_bp.route('/users', methods=["POST"])
def register_user():
    try:
        user_schema = UserCreateSchema(**request.get_json())
    except ValidationError as error:
        return jsonify({"errors": error.errors(include_url=False, include_context=False)}), 400
    
    new_user = create_user_instance(user_schema)
 
    response = {'user': new_user.info_dict()}
 
    return jsonify(response)


@user_bp.route('/users/<int:id>', methods=["GET"])
def get_user_info(id: int):
    user = User.query.get(id)
    
    if not user:
        return create_error_response(ErrorCode.USER_NOT_FOUND)

    response = {'user': user.info_dict()}
    return jsonify(response)


@user_bp.route('/users/<int:id>', methods=["PUT"])
def edit_user(id: int):
    try:
        user_schema = UserEditSchema(**request.get_json())
    except ValidationError as error:
        return jsonify({"errors": error.errors(include_url=False, include_context=False)}), 400
    
    user: User = User.query.get(id)
    if not user:
        return create_error_response(ErrorCode.USER_NOT_FOUND)
    
    new_data = user_schema.model_dump(exclude_unset=True)
    # Update the values
    for key, value in new_data.items():
        setattr(user, key, value)
    
    try:
        db.session.commit()
    except Exception as e:
        # TODO: log that
        return create_error_response(ErrorCode.UNKNOWN)
 
    response = {'user': user.info_dict()}
 
    return jsonify(response)