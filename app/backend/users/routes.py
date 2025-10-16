from flask.blueprints import Blueprint
from backend.users.models import User
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
def create_user():

    new_user = User(**request.get_json())
    db.session.add(new_user)
    db.session.commit()

    return jsonify(request.get_json())
