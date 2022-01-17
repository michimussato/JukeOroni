"""
Django settings for jukeoroni project.

Generated by 'django-admin startproject' using Django 3.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""
import logging
import os

from jukeoroni._secrets import DJANGO_SECRET_KEY
from pathlib import Path
from player.jukeoroni.settings import (
    MEDIA_ROOT,
    DJANGO_LOGGING_LEVEL,
)


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# For JukeOroni is this probably not a big issue
SECRET_KEY = DJANGO_SECRET_KEY

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '[%(asctime)s] [%(levelname)s] [%(threadName)s|%(thread)d] [%(name)s]: %(message)s',
            'datefmt': '%m-%d-%Y %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'ERROR',
            # 'class': 'logging.FileHandler',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'filename': os.path.join(MEDIA_ROOT, 'jukeoroni_logs', 'django_error.log'),
            'formatter': 'simple',
        },
        'file_juke_box': {
            'level': 'DEBUG',
            # 'class': 'logging.FileHandler',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'filename': os.path.join(MEDIA_ROOT, 'jukeoroni_logs', 'jukebox_error.log'),
            'formatter': 'simple',
        },
        'file_meditation_box': {
            'level': 'DEBUG',
            # 'class': 'logging.FileHandler',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'filename': os.path.join(MEDIA_ROOT, 'jukeoroni_logs', 'meditationbox_error.log'),
            'formatter': 'simple',
        },
        'file_create_update_track_list': {
            'level': 'DEBUG',
            # 'class': 'logging.FileHandler',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'midnight',
            'interval': 1,
            'backupCount': 7,
            'filename': os.path.join(MEDIA_ROOT, 'jukeoroni_logs', 'create_update_track_list_error.log'),
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['console', 'file'],
            # 'propagate': False,
            'level': 'DEBUG',
        },
        'asyncio': {
            'handlers': ['console', 'file'],
            # 'propagate': True,
            'level': 'WARNING',
        },
        'player.jukeoroni.juke_box': {
            'handlers': ['file_juke_box'],
            # 'propagate': True,
            'level': 'DEBUG',
        },
        'player.jukeoroni.meditation_box': {
            'handlers': ['file_meditation_box'],
            # 'propagate': True,
            'level': 'DEBUG',
        },
        'player.jukeoroni.create_update_track_list': {
            'handlers': ['file_create_update_track_list'],
            # 'propagate': True,
            'level': 'DEBUG',
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'file']
    }
}


LOG = logging.getLogger(__name__)
LOG.setLevel(DJANGO_LOGGING_LEVEL)


ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'player.apps.PlayerConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
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

ROOT_URLCONF = 'jukeoroni.urls'

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

WSGI_APPLICATION = 'jukeoroni.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        # 'NAME': BASE_DIR / '..' / 'db.sqlite3',
    }
}

LOG.critical(f'USING DB {str(os.path.abspath(DATABASES["default"]["NAME"]))}')

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

# TIME_ZONE = 'UTC'
TIME_ZONE = 'Europe/Zurich'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

# STATIC_ROOT = '/data/venv/lib/python3.7/site-packages/django/contrib/admin'

STATIC_URL = '/static/'
STATIC_ROOT = [os.path.join(BASE_DIR, 'static'), ]

# STATICFILES_DIRS = [
#     BASE_DIR / "static",
#     '/data/venv/lib/python3.7/site-packages/django/contrib/admin',
# ]

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
