from slugify import slugify as py_slugify
from random import randint


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
