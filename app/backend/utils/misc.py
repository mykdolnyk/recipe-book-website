from flask import abort, jsonify
from pydantic import BaseModel, ValidationError
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
        logger.exception(e)
        return create_error_response(ErrorCode.UNKNOWN)
    
    
def parse_to_schema(schema_class: BaseModel, request):
    """Parses the data from the `request` object and returns the schema. If
    the data is invalid, aborts with an error dict."""
    try:
        return schema_class(**request.get_json())
    except ValidationError as error:
        abort(jsonify({"errors": error.errors(include_url=False, include_context=False)}), 400)
    
    
def create_object_from_request(request, db_model, create_schema, get_schema, db, logger):
    schema = parse_to_schema(schema_class=create_schema, 
                             request=request)
    
    new_object = db_model(**schema.model_dump())
    
    db.session.add(new_object)
    error_response = safe_commit(db, logger)
    if error_response:
        return error_response

    response = get_schema.model_validate(new_object).model_dump()
    
    return response