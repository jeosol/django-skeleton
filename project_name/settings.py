"""
Django settings for {{ project_name }} project.

Generated by 'django-admin startproject' using Django 2.0.5.

For more information on this file, see
https://docs.djangoproject.com/en/{{ docs_version }}/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/{{ docs_version }}/ref/settings/
"""

import os
import dj_database_url
import email.utils
import ipaddress
from glob import glob

from decouple import config
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from django.core.checks import Error, Warning, register
from django.conf import settings

from .check_utils import expected_settings

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/{{ docs_version }}/howto/deployment/checklist/

SECRETS_DIR = os.path.abspath(os.path.join(os.path.sep, 'run', 'secrets'))
ALL_SECRETS = os.path.join(SECRETS_DIR, '*')

SWARM_MODE = config('SWARM_MODE', cast=bool, default=False)

if SWARM_MODE:
    # Export variables from secrets
    for secret in glob(ALL_SECRETS):
        secret_key = secret.split('/')[-1].upper()
        with open(secret) as secret_file:
            secret_value = secret_file.read().rstrip('\n')
            os.environ[secret_key] = secret_value

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='z9($i(5-)ofq(2)ju7d0xdapc8xj9$#-ptjfc+y+u4a5!&n@*v')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', cast=bool, default=True)

ADMINS = []
if config('ADMINS', default=None):
    ADMINS = email.utils.getaddresses(config('ADMINS', default=None).split(','))

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '.ngrok.io']

# Calculate list of ip addresses from CIDR
if config('ALLOWED_CIDR', default=None):
    networks = config('ALLOWED_CIDR', default=None).split(',')

    allowed_ips = []
    for network in networks:
        allowed_ips.extend([str(ip) for ip in ipaddress.ip_network(network)])
    ALLOWED_HOSTS.extend(allowed_ips)

if config('ALLOWED_HOSTS', default=None):
    ALLOWED_HOSTS.extend(config('ALLOWED_HOSTS', default=None).split(','))

# Application definition

INSTALLED_APPS = [
    'django_pdb',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'users.apps.UsersConfig',

    'anymail',
    'corsheaders',
    'django_celery_beat',
    'django_extensions',
    'django_filters',
    'guardian',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_swagger',
    'storages',

    # Health checks
    'health_check',
    'health_check.db',
    'health_check.cache',
    'health_check.contrib.celery',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = '{{ project_name }}.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
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

WSGI_APPLICATION = '{{ project_name }}.wsgi.application'

# Database
# https://docs.djangoproject.com/en/{{ docs_version }}/ref/settings/#databases


DATABASE_URL = config('DATABASE_URL', default=None)
if DATABASE_URL is None:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': '{{ project_name }}',
        }
    }
else:
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=500)
    }

# Password validation
# https://docs.djangoproject.com/en/{{ docs_version }}/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/{{ docs_version }}/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = config('TIME_ZONE', default='GMT')

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/{{ docs_version }}/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = 'staticfiles'

AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default=None)
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default=None)
AWS_STORAGE_BUCKET_NAME = config('AWS_STORAGE_BUCKET_NAME', default=None)
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}
AWS_QUERYSTRING_AUTH = True  # signed URLs to avoid static files misuse
AWS_S3_REGION_NAME = config('AWS_S3_REGION_NAME', default='us-east-1')
if not DEBUG:
    AWS_S3_ENCRYPTION = True

if not DEBUG:
    DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
    AWS_S3_CUSTOM_DOMAIN = config('AWS_S3_CUSTOM_DOMAIN', default=None)

MEDIA_URL = '/media/'
MEDIA_ROOT = 'media'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.BasicAuthentication'
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser'
    )
}

if DEBUG:
    CORS_ORIGIN_ALLOW_ALL = True

AUTH_USER_MODEL = 'users.Account'

MEMCACHED_HOST = config('MEMCACHED_HOST', default=None)
if MEMCACHED_HOST:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '{}:11211'.format(MEMCACHED_HOST),
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }

sentry_sdk.init(
    dsn=config('SENTRY_DSN', default=''),
    integrations=[DjangoIntegration()],
    release=config('DRONE_COMMIT_SHORT', default=''),
    send_default_pii=True,
    request_bodies='always'
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        }
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': config('LOGGING_LEVEL', default='INFO'),
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': config('LOGGING_LEVEL', default='INFO'),
            'propagate': False,
        },
    }
}

REDIS_URL = config('REDIS_URL', default='redis://localhost:6379')
CELERY_BROKER_URL = f'{REDIS_URL}/0'
CELERY_RESULT_BACKEND = f'{REDIS_URL}/1'

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

ENVIRONMENT_CHECKS = config('ENVIRONMENT_CHECKS', default='develop')


@register(deploy=True)
def check_settings(app_configs, **kwargs):
    messages = []
    all_values = expected_settings(settings)
    environment = settings.ENVIRONMENT_CHECKS

    current = all_values.current
    expected = all_values.develop
    if environment == 'staging':
        expected = all_values.staging
    elif environment == 'production':
        expected = all_values.production

    error_counter = 1
    warning_counter = 1

    for key, value in expected.items():
        if config(key, default=None) is None:
            messages.append(
                Warning(
                    f'Environment variable: {key} is None. Default value set: {current.get(key)}',
                    hint=f'Update environment variable: {key}={expected.get(key)} for environment: {environment}',
                    obj=settings,
                    id=f'settings.W{str(warning_counter).zfill(3)}'
                )
            )
        if current.get(key) is None:
            messages.append(
                Warning(
                    f'Current {key}: {current.get(key)} is None',
                    hint=f'Provide a value for {key}',
                    obj=settings,
                    id=f'settings.W{str(warning_counter).zfill(3)}'
                )
            )
        if current.get(key) != expected.get(key):
            messages.append(
                Error(
                    f'Current {key}: {current.get(key)} is different from expected: {expected.get(key)} for environment: {environment}',
                    hint=f'Update value for {key}={expected.get(key)} for environment: {environment}',
                    obj=settings,
                    id=f'settings.E{str(error_counter).zfill(3)}'
                )
            )
        error_counter += 1
        warning_counter += 1

    # DRONE_COMMIT_SHORT is passed as env variable from ci automation. It is used to track logging in Sentry.
    if config('DRONE_COMMIT_SHORT', default=None) is None:
        messages.append(
            Warning(
                f'Environment variable: DRONE_COMMIT_SHORT is None. Default value set: \'\'',
                hint=f'Update environment variable: DRONE_COMMIT_SHORT for environment: {environment}',
                obj=settings,
                id=f'settings.W{str(warning_counter+1).zfill(3)}'
            )
        )
    return messages