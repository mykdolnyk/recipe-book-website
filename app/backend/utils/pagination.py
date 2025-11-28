from flask import abort
from pydantic import BaseModel
from sqlalchemy.orm import Query


def paginate(request_args: dict, sqlalchemy_query: Query, pydantic_model: BaseModel, **kwargs):
    try:
        page = int(request_args.get('page', 1))
        per_page = int(request_args.get(
            'per-page', kwargs.get('per_page', 5)))
    except ValueError:
        abort(400)

    pagination = sqlalchemy_query.paginate(page=page,
                                           per_page=per_page,
                                           max_per_page=kwargs.get(
                                               'max_per_page', 25),
                                           error_out=False)

    obj_list = [pydantic_model.model_validate(obj).model_dump()
                for obj in pagination.items]

    return {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        kwargs.get('list_name', "item_list"): obj_list,
    }