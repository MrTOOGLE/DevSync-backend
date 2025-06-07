import os

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG") == "True"

ALLOWED_HOSTS = ["*"] # os.getenv("ALLOWED_HOSTS").strip().split(",")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'channels',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'djoser',
    'django_filters',

    'users.apps.UsersConfig',
    'api.apps.ApiConfig',
    'projects.apps.ProjectsConfig',
    'voting.apps.VotingConfig',
    'roles.apps.RolesConfig',
    'notifications.apps.NotificationsConfig',

    'django_cleanup.apps.CleanupConfig'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'corsheaders.middleware.CorsMiddleware',
    'config.middleware.RequestLoggingMiddleware',
    'users.middleware.UserActivityMiddleware'
]

CORS_ORIGIN_ALLOW_ALL = True

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

ASGI_APPLICATION = 'config.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': "django.db.backends.postgresql",
        'NAME': os.getenv("POSTGRES_DB"),
        'USER': os.getenv("PG_BOUNCER_USER"),
        'PASSWORD': os.getenv("PG_BOUNCER_PASSWORD"),
        'HOST': os.getenv("PG_BOUNCER_HOST"),
        'PORT': int(os.getenv("PG_BOUNCER_PORT")),
        "OPTIONS": {
            "sslmode": "disable",
        },
        "CONN_MAX_AGE": 300,
    }
}

"""
DATABASES = {
    'default': {
        'ENGINE': "django.db.backends.postgresql",
        'NAME': os.getenv("POSTGRES_DB"),
        'USER': os.getenv("POSTGRES_USER"),
        'PASSWORD': os.getenv("POSTGRES_PASSWORD"),
        'HOST': os.getenv("POSTGRES_HOST"),
        'PORT': int(os.getenv("POSTGRES_PORT")),
        "OPTIONS": {
            "sslmode": "disable",
        },
        "CONN_MAX_AGE": 300,
    }
}
"""

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = os.getenv("LANGUAGE_CODE")
TIME_ZONE = os.getenv("TIME_ZONE")
USE_I18N = os.getenv("USE_I18N") == 'True'
USE_TZ = os.getenv("USE_TZ") == 'True'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'

# static files
STATIC_URL = '/static/'
STATIC_ROOT = 'static'
STATICFILES_DIRS = []

# media files
MEDIA_ROOT = BASE_DIR / 'media/'
MEDIA_URL = '/media/'

# rest framework
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
}

# djoser

DJOSER = {
    'SERIALIZERS': {
        'token_create': 'users.serializers.TokenCreateSerializer',
    }
}

# auth settings
EMAIL_VERIFICATION_CODE_LIFETIME = int(os.getenv("EMAIL_VERIFICATION_CODE_LIFETIME"))
EMAIL_VERIFICATION_CODE_RESEND_TIMEOUT = int(os.getenv("EMAIL_VERIFICATION_CODE_RESEND_TIMEOUT"))
EMAIL_VERIFICATION_MAX_ATTEMPTS = int(os.getenv("EMAIL_VERIFICATION_MAX_ATTEMPTS"))
EMAIL_VERIFICATION_SUBJECT = os.getenv("EMAIL_VERIFICATION_SUBJECT")

# smtp
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL")
EMAIL_TEST_HOST_USER = os.getenv("EMAIL_TEST_HOST_USER")

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER
EMAIL_ADMIN = EMAIL_HOST_USER

# redis and celery
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# caching
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}
VERIFICATION_CODE_CACHE_KEY = "code:{username}"
PUBLIC_PROJECTS_CACHE_KEY = 'public_projects:{urlencode}'

# logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '''
                {
                    "timestamp": "%(asctime)s",
                    "level": "%(levelname)s",
                    "logger": "%(name)s",
                    "message": "%(message)s",
                    "request": %(request)s,
                    "response": %(response)s
                }
            ''',
        },
        'simple': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        }
    },

    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        }
    },

    'handlers': {
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },

        'file': {
            'level': 'INFO',
            'class': 'config.logging_handlers.DailyRotatingFileHandler',
            'filename': 'server.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
        },

        'file_request': {
            'level': 'INFO',
            'class': 'config.logging_handlers.DailyRotatingFileHandler',
            'filename': 'requests.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'json',
            'encoding': 'utf-8',
        },

        'sql': {
            'level': 'DEBUG',
            'class': 'config.logging_handlers.DailyRotatingFileHandler',
            'filename': 'sql.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
            'encoding': 'utf-8',
            'filters': ['require_debug_true'],
        },

        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
    },

    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },

        'users': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },

        'django.server': {
            'handlers': ['django.server'],
            'level': 'DEBUG',
            'propagate': False,
        },

        'requests': {
            'handlers': ['console', 'file_request'],
            'level': 'DEBUG',
            'propagate': False,
        },

        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },

        'django.db.backends': {
            'handlers': ['sql'],
            'level': 'DEBUG',
            'propagate': False,
        },
    }
}

REQUEST_LOGGING = {
    "EXCLUDE_PATHS": [],
    "SENSITIVE_KEYS": ['password', 'token'],
}

# django channels
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'config.utils.redis_channel.ExtendedRedisChannelLayer',
        'CONFIG': {
            'hosts': [(REDIS_HOST, REDIS_PORT)],
        },
    },
}

# general
PROJECT_INVITATION_EXPIRY_DAYS = 7
INVITATION_IS_EXPIRED_MESSAGE = 'Приглашение истекло. Запросите новое или проигнорируйте!'
