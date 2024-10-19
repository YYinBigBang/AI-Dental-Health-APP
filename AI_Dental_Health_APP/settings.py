"""
Django settings for AI_Dental_Health_APP project.

Generated by 'django-admin startproject' using Django 5.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.0/ref/settings/
"""

import os
from pathlib import Path
from datetime import timedelta

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# define log file path
LOG_DIR = BASE_DIR / 'django_logs'
LOG_DIR.mkdir(exist_ok=True)
os.chmod(LOG_DIR, 0o755)

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Line Bot Settings
LINE_CHANNEL_ACCESS_TOKEN = 'QE0kErTgy/3bNpUKFMJ76XR1AyRO2xAjPPKdlTg2Fx3uXN21paS+R7KvozDMD5Taq6Xz893vWP4jMjRlQcMqcarRqv51bZ2D5lhEifrqGa6/dcJgbKx3pBbzyyQqKxbsqEP5vSsnbglwPHNowMw5lQdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = 'f95281bf06be5fb105f84d12b356c0dc'


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-5js!+$ccs8=n-j52pd8uz_z2nnhg@4$iyb&645%4g-riz_=q7!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/
LANGUAGE_CODE = 'zh-tw'

# set the timezone to Taipei.
TIME_ZONE = 'Asia/Taipei'
# Enable timezone-aware datetimes.
USE_TZ = True
# Enable translation of strings.
USE_I18N = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'user_management.User'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # Allow session-based validation
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'AI_Dental_Health_APP.django_utils.custom_exception_handler',
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=3),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=3),
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

SPECTACULAR_SETTINGS = {
    'TITLE': 'Dental Health API',
    'DESCRIPTION': 'Takes photo of teeth and analyze the dental plaque count.',
    'VERSION': '3.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

ALLOWED_HOSTS = ['*']
# ALLOWED_HOSTS = [
#     'localhost',
#     '127.0.0.1',
#     '10.140.0.2',
#     'ai-dental-health-app-l3ewwtueeq-de.a.run.app',  # haoyu@
#     'dental-health-app.jieniguicare.org',
#     'gcp.jieniguicare.org',
#     'jieniguicare.org',
#     '35.221.203.201',
#     'ai-dental-health-app-f2rwv6be2a-de.a.run.app',
# ]


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'drf_spectacular',
    'dental_health_service',
    'user_management',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'AI_Dental_Health_APP.urls'

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

WSGI_APPLICATION = 'AI_Dental_Health_APP.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DATABASE_NAME', 'ai_dental_db'),
        'USER': os.environ.get('DATABASE_USER', 'ai_dental_user'),
        'PASSWORD': os.environ.get('DATABASE_PASSWORD', '@squirtle1234#'),
        'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
        'PORT': os.environ.get('DATABASE_PORT', '5432'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators
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


# logger configuration
# https://docs.djangoproject.com/en/5.0/ref/logging/
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(levelname)s [%(funcName)s]: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        },
        'server': {
            'level': 'INFO',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': str(LOG_DIR / 'server.log'),  # basic file name
            'when': 'midnight',  # shift at midnight
            'interval': 1,  # every <1> days
            'backupCount': 14,  # backup files are capped at 14 files.
            'formatter': 'standard',
        },
        'django_error': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'error.log'),
            'formatter': 'standard'
        },
        'root': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': str(LOG_DIR / 'root.log'),
            'formatter': 'standard'
        },
    },
    'loggers': {
        # "" is root logger which captures all log messages that are not handled by other named loggers
        'root': {
            'handlers': ['root'],
            'level': 'DEBUG',
            'propagate': True,
        },
        # "django" will log all messages generated by Django's internal processes
        'django': {
            'handlers': ['server', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        # "django.server" will log only starting with the runserver command
        'django.server': {
            'handlers': ['server', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        # "django.request" will log only 4xx and 5xx requests
        'django.request': {
            'handlers': ['django_error'],
            'level': 'DEBUG',
            'propagate': True,
        },
        # "django.security" will log any occurrence of SuspiciousOperation and other security-related errors.
        'django.security': {
            'handlers': ['django_error'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

