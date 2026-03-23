import os
from pathlib import Path

SECRET_KEY = os.getenv('FLASK_SECRET_KEY')

BASE_DIR = Path(__file__).resolve().parent

SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"

REDIS_URL = os.getenv('REDIS_URL')
CELERY_CONFIG = {
    "broker_url": REDIS_URL,
    "result_backend": REDIS_URL,
    "task_ignore_result": True,
}

RATE_LIMIT_ENABLED = True
RATE_LIMIT_COOLDOWN = 60 * 10
RATE_LIMIT_MAX_REQUESTS = 500

LOGIN_ATTEMPTS_MAX = 5
LOGIN_RESTRICTION_TIMEOUT = 60 * 15

CSRF_PROTECTION = True

STATIC_URL_PATH = Path('/static')
FIXTURES_DIR = BASE_DIR / 'fixtures'

PASSWORD_POLICY = {
    'length': 8,
    'uppercase': 1,
    'numbers': 1,
    'special': 1,
    'entropybits': 20,
    'strength': 0.66,
}

LOG_DIR = Path('/var/log/web/')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'default': {
            'format': '%(asctime)s - %(levelname)s in %(funcName)s, %(filename)s: %(message)s'
        },
        'verbose': {
            'format': '%(asctime)s - %(levelname)s in %(funcName)s, %(pathname)s on line %(lineno)d by %(name)s: %(message)s'
        }
    },

    'handlers': {
        'stdout': {
            'level': 'INFO',
            'formatter': 'default',
            'class': 'logging.StreamHandler'
        },
        'error_log': {
            'level': 'ERROR',
            'formatter': 'verbose',
            'class': 'logging.FileHandler',
            'filename': LOG_DIR / 'error.log'
        }
    },

    'loggers': {
        'backend.users.routes': {
            'handlers': {'stdout', 'error_log'},
            'level': 'INFO',
            'propagate': False
        },
        'backend.recipes.routes': {
            'handlers': {'stdout', 'error_log'},
            'level': 'INFO',
            'propagate': False
        },
        'backend.utils.misc': {
            'handlers': {'stdout', 'error_log'},
            'level': 'INFO',
            'propagate': False
        },
    },

    'root': {
        'handlers': ['error_log'],
        'level': 'ERROR'
    }
}


LOAD_EXAMPLE_FIXTURES = True 
"""Makes it so the `load_fixtures` function loads the fixtures from `app\\fixtures\\example\\` dir.
It may be enabled **only** for demonstrational purposes, and disabled for production/real use.
"""