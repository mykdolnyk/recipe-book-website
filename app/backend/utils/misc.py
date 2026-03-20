from logging import getLogger
from flask import jsonify, request
from pydantic import BaseModel, ValidationError
from slugify import slugify as py_slugify
from random import randint
from backend.utils.errors import create_error_response
from sqlalchemy import inspect


logger = getLogger(name=__name__)


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


def safe_commit(session):
    """Commits DB changes in a save way, loggin any exceptions into the `logger`.
    Reraises an exception if there was one, or returns `None` if not."""
    try:
        session.commit()
        return None
    except Exception as exc:
        session.rollback()
        logger.exception(exc)
        raise exc


class ObjectManager:
    def __init__(self, db_model, create_schema=None, update_schema=None, get_schema=None):
        self.db_model = db_model
        self.create_schema: BaseModel = create_schema
        self.update_schema: BaseModel = update_schema
        self.get_schema: BaseModel = get_schema
        self.object = None
        self.success = None
        self._session = db_model.query.session
        self._errors = []
        self.schema_data = None
        
    def create_object(self, data: dict, exclude_for_db: list | None = None, commit=True):
        try:
            schema = self.create_schema(**data)
            self.schema_data = schema
        except ValidationError as error:
            self._errors.append(error)
            self.success = False
            return None

        # Create DB object
        new_object = self.db_model(**schema.model_dump(exclude=exclude_for_db))
        self.object = new_object
        self._session.add(new_object)

        if commit:
            self.commit_changes()
            if self._errors:
                return None

        self.success = True
        return new_object
    
    def update_object(self, obj, data: dict, commit=True):
        self.object = obj
        try:
            schema = self.update_schema(**data)
            self.schema_data = schema
        except ValidationError as error:
            self._errors.append(error)
            self.success = False
            return None

        # Update DB object
        new_data = schema.model_dump(exclude_unset=True)
        
        for key, value in new_data.items():
            # Check if the field is a relationship (m2m)
            mapper = inspect(obj).mapper
            if key in mapper.relationships:
                # Obtain the model instance from the relationship
                related_model = mapper.relationships[key].mapper.class_
                # Get the objects
                model_objects = related_model.query.filter(related_model.id.in_(value)).all()
                # Set them
                setattr(obj, key, model_objects)
            else:
                # Usual set operation
                setattr(obj, key, value)

        if commit:
            self.commit_changes()
            if self._errors:
                return None

        self.object = obj
        self.success = True
        return obj
    
    def generate_response(self):
        if not self._errors:
            response = self.get_schema.model_validate(self.object).model_dump()
            return jsonify(response), 200
        else:
            return create_error_response(*self._errors)

    def commit_changes(self):
        try:
            safe_commit(self._session)
        except Exception as error:
            self._errors.append(error)
            self.success = False
            return None


def get_ip_address() -> str:
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        return request.environ['REMOTE_ADDR']
    else:
        return request.environ['HTTP_X_FORWARDED_FOR'] # if behind a proxy
