from typing import Tuple
from flask import Response, jsonify
from pydantic import ValidationError
from slugify import slugify as py_slugify
from random import randint
from backend.utils.errors import ErrorCode, create_error_response


def slugify(text: str, additional_id: bool = False):
    slug = py_slugify(text)
    if additional_id:
        # Append a random hexidecimal value between 0001 and FFFFF
        slug += f'-{randint(1, 0xFFFFF):05x}'
    return slug


def generate_unique_slug(text: str, model_class) -> str:
    slug = slugify(text)
    # Append a unique ID, retry if the same slug exists
    while True:
        if model_class.query.filter_by(slug=slug).first():
            slug = slugify(text, additional_id=True)
        else:
            break
    return slug


def safe_commit(db, logger):
    """Commits DB changes in a save way, loggin any exceptions into the `logger`.
    Returns an error repsonse if there was an exception, or `None` if not."""
    try:
        db.session.commit()
        return None
    except Exception as e:
        db.session.rollback()
        logger.exception(e)
        return create_error_response(ErrorCode.UNKNOWN)


def create_object_from_dict(data: dict, db_model, create_schema,
                            get_schema, db, logger,
                            exclude_for_db: list | None = None) -> Tuple[Response, int]:

    # Get and validate schema
    try:
        schema = create_schema(**data)
    except ValidationError as error:
        return jsonify({"errors": error.errors(include_url=False, include_context=False)}), 400

    # Create DB object
    new_object = db_model(**schema.model_dump(exclude=exclude_for_db))
    db.session.add(new_object)
    error_response = safe_commit(db, logger)
    # If errors occur during the commit - return error response
    if error_response:
        return error_response

    # Get a response
    response = get_schema.model_validate(new_object).model_dump()
    return jsonify(response), 200


def update_object_from_dict(obj, data: dict, update_schema,
                            get_schema, db, logger) -> Tuple[Response, int]:
    # Get and validate schema
    try:
        schema = update_schema(**data)
    except ValidationError as error:
        return jsonify({"errors": error.errors(include_url=False, include_context=False)}), 400

    # Update DB object
    new_data = schema.model_dump(exclude_unset=True)
    for key, value in new_data.items():
        setattr(obj, key, value)
    
    error_response = safe_commit(db, logger)
    # If errors occur during the commit - return error response
    if error_response:
        return error_response

    # Get a response
    response = get_schema.model_validate(obj).model_dump()
    return jsonify(response), 200
