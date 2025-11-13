from pathlib import Path

SECRET_KEY = 'not-so-secret-key'

BASE_DIR = Path(__file__).resolve().parent

SQLALCHEMY_DATABASE_URI = "sqlite:///dev.db"

PASSWORD_POLICY = {
    'length': 8,
    'uppercase': 1,
    'numbers': 1,
    'special': 1,
    'entropybits': 20,
    'strength': 0.66,
}

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
            'filename': BASE_DIR / 'error.log'
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
    },

    'root': {
        'handlers': ['error_log'],
        'level': 'ERROR'
    }
}
