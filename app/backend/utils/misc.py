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