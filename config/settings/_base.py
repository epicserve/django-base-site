import contextlib
import socket
from functools import partial
from pathlib import Path

from django.utils.crypto import get_random_string

from django_envtools import Env

"""
Django settings for config project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""


get_secret_key = partial(get_random_string, length=50, allowed_chars="abcdefghijklmnopqrstuvwxyz0123456789!@%^&*-_=")


BASE_DIR = Path(__file__).parent.parent.parent  # type: ignore

env = Env()

READ_DOT_ENV_FILE = env.bool("READ_DOT_ENV_FILE", default=True)

if READ_DOT_ENV_FILE is True:
    env.read_env(str(BASE_DIR.joinpath(".env")))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env.str(
    "SECRET_KEY",
    help_text="Django's secret key, see"
    "https://docs.djangoproject.com/en/dev/ref/settings/#secret-key for more information",
    initial_func=get_secret_key,
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False, initial="on", help_text="Set to `on` to enable debugging")

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[],
    help_text="List of allowed hosts (e.g., `127.0.0.1,example.com`), see "
    "https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts for more information",
)

INTERNAL_IPS = env.list(
    "INTERNAL_IPS",
    default=["127.0.0.1"],
    initial="127.0.0.1,0.0.0.0",
    help_text="IPs that are allowed to use debug() (e.g., `127.0.0.1,example.com`), see "
    "https://docs.djangoproject.com/en/dev/ref/settings/#internal-ips for more information",
)

# Get the IP to use for Django Debug Toolbar when developing with docker
if (
    env.bool(
        "USE_DOCKER", default=False, help_text="Boolean used to add docker's internal ip to the `INTERNAL_IPS` setting"
    )
    is True
):
    ip = socket.gethostbyname(socket.gethostname())
    INTERNAL_IPS += [ip[:-1] + "1"]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.base",
    "apps.accounts",
    "maintenance_mode",
    "allauth",
    "allauth.account",
    "crispy_forms",
    "crispy_bootstrap5",
    "django_envtools",
    "storages",
]

MIDDLEWARE = [
    "allauth.account.middleware.AccountMiddleware",
    "django_alive.middleware.healthcheck_bypass_host_check",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "maintenance_mode.middleware.MaintenanceModeMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "maintenance_mode.context_processors.maintenance_mode",
                "apps.base.context_processors.site_name",
            ],
        },
    },
]

WSGI_APPLICATION = env.str(
    "WSGI_APPLICATION",
    default="config.wsgi.application",
    help_text="WSGI application callable, see https://docs.djangoproject.com/en/dev/ref/settings/#wsgi-application for "
    "more information",
)
DB_SSL_REQUIRED = env.bool(
    "DB_SSL_REQUIRED",
    default=not DEBUG,
    help_text="Set to `on` to require SSL for database connections, default is `off` when DEBUG is `on`",
)

DATABASES = {
    "default": env.dj_db_url(
        "DATABASE_URL",
        default="postgres://postgres@postgres/postgres",
        ssl_require=DB_SSL_REQUIRED,
        initial="postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}",
        help_text="Database URL for the default database, see https://github.com/jacobian/dj-database-url for "
        "more examples",
    )
}

# Custom User Model
# https://docs.djangoproject.com/en/dev/topics/auth/customizing/#substituting-a-custom-user-model
AUTH_USER_MODEL = "accounts.User"

# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True


USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

DEFAULT_FILE_STORAGE = env.str(
    "DEFAULT_FILE_STORAGE",
    default="django.core.files.storage.FileSystemStorage",
    help_text="Default file storage backend, see https://docs.djangoproject.com/en/dev/ref/settings/#storages for "
    "more information",
)
STATICFILES_STORAGE = env.str(
    "DEFAULT_FILE_STORAGE",
    default="django.core.files.storage.FileSystemStorage",
    help_text="Default file storage for staticfiles, see https://docs.djangoproject.com/en/dev/ref/settings/#storages "
    "for more information",
)
STORAGES = {
    "default": {
        "BACKEND": DEFAULT_FILE_STORAGE,
    },
    "staticfiles": {
        "BACKEND": STATICFILES_STORAGE,
    },
}


if STORAGES["default"]["BACKEND"].endswith("MediaS3Storage") is True:
    STORAGES["staticfiles"]["BACKEND"] = STATICFILES_STORAGE
    AWS_ACCESS_KEY_ID = env.str("AWS_ACCESS_KEY_ID", help_text="AWS Access Key ID for S3 storage")
    AWS_SECRET_ACCESS_KEY = env.str("AWS_SECRET_ACCESS_KEY", help_text="AWS Secret Access Key for S3 storage")
    AWS_STORAGE_BUCKET_NAME = env.str("AWS_STORAGE_BUCKET_NAME", help_text="AWS S3 Bucket Name for storage")
    AWS_DEFAULT_ACL = "public-read"
    AWS_S3_REGION = env.str("AWS_S3_REGION", default="us-east-1", help_text="AWS S3 Region for storage")
    AWS_S3_CUSTOM_DOMAIN = f"s3.{AWS_S3_REGION}.amazonaws.com/{AWS_STORAGE_BUCKET_NAME}"
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    STATIC_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/static/"
    MEDIA_URL = f"https://{AWS_S3_CUSTOM_DOMAIN}/media/"
    STATICFILES_DIRS = [str(BASE_DIR.joinpath("public", "static"))]

else:
    # Local Storage
    PUBLIC_ROOT = BASE_DIR.joinpath("public")
    STATIC_ROOT = BASE_DIR.joinpath("collected_static")
    MEDIA_ROOT = PUBLIC_ROOT.joinpath("media")
    PUBLIC_STATIC = PUBLIC_ROOT.joinpath("static")
    STATICFILES_DIRS = [str(PUBLIC_STATIC)]
    MEDIA_URL = "/public/media/"
    STATIC_URL = "/public/static/"

# Default primary key field type
# https://docs.djangoproject.com/en/dev/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CACHE SETTINGS
REDIS_URL = env.str(
    "REDIS_URL",
    default="redis://redis:6379/0",
    help_text="URL used to connect to Redis, see https://docs.djangoproject.com/en/dev/ref/settings/#location for "
    "more information",
)
REDIS_PREFIX = env.str(
    "REDIS_PREFIX",
    default="",
    help_text="Prefix for all Redis keys, useful to avoid key collisions in shared Redis instances",
)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
        "KEY_PREFIX": REDIS_PREFIX,
    }
}

# CELERY SETTINGS
# Celery configuration docs: https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html#configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_BROKER_TRANSPORT_OPTIONS = {"global_keyprefix": REDIS_PREFIX}

# CRISPY-FORMS
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

SESSION_ENGINE = "django.contrib.sessions.backends.cache"

SITE_ID = 1
SITE_NAME = "Django Base Site"

# DJANGO DEBUG TOOLBAR SETTINGS
if DEBUG is True:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    DEBUG_TOOLBAR_CONFIG = {"INTERCEPT_REDIRECTS": False}

# ALLAUTH SETTINGS (https://django-allauth.readthedocs.io/en/latest/configuration.html)
AUTHENTICATION_BACKENDS = ["allauth.account.auth_backends.AuthenticationBackend"]
LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*"]
# This is set to "none" so when trying out an app idea you don't have to have sending emails setup, which can be a pain.
# It's not recommended to leave it as none on a production system. Choose either mandatory or optional.
ACCOUNT_EMAIL_VERIFICATION = "none"

# CUSTOM Django Base Site ALLAUTH settings used in the custom adapter (apps.accounts.auth_adapter)
ACCOUNT_ADAPTER = "apps.accounts.auth_adapter.AccountAdapter"
ACCOUNT_SIGNUP_OPEN = False
ACCOUNT_SHOW_POST_LOGIN_MESSAGE = False

email = env.dj_email_url(
    "EMAIL_URL",
    default="smtp://skroob@planetspaceball.com:12345@smtp.planetspaceball.com:587/?ssl=True&_default_from_email=President%20Skroob%20%3Cskroob@planetspaceball.com%3E",
    help_text="Email URL for sending emails, see https://github.com/migonzalvar/dj-email-url for more examples",
)
DEFAULT_FROM_EMAIL = email["DEFAULT_FROM_EMAIL"]
EMAIL_HOST = email["EMAIL_HOST"]
EMAIL_PORT = email["EMAIL_PORT"]
EMAIL_HOST_PASSWORD = email["EMAIL_HOST_PASSWORD"]
EMAIL_HOST_USER = email["EMAIL_HOST_USER"]
EMAIL_USE_TLS = email["EMAIL_USE_TLS"]


def log_format() -> str:
    """Dump all available values into the JSON log output."""
    keys = (
        "asctime",
        "created",
        "levelname",
        "levelno",
        "filename",
        "funcName",
        "lineno",
        "module",
        "message",
        "name",
        "pathname",
        "process",
        "processName",
    )
    return " ".join([f"%({i:s})" for i in keys])


log_level = "WARNING"
IS_DEBUG_LOGGING_ON = env.bool("IS_DEBUG_LOGGING_ON", default=False, help_text="Set to `on` to enable debug logging")
if IS_DEBUG_LOGGING_ON is True:
    log_level = "DEBUG"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": log_format(),
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
        },
    },
    "handlers": {
        # console logs to stderr
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "loggers": {
        # default for all Python modules not listed below
        "": {
            "level": log_level,
            "handlers": ["console"],
        },
    },
}

# setup pretty logging for local dev
with contextlib.suppress(ModuleNotFoundError):
    import readable_log_formatter  # noqa: F401

    LOGGING["formatters"]["default"]["class"] = "readable_log_formatter.ReadableFormatter"  # type: ignore

# MAINTENANCE MODE SETTINGS
MAINTENANCE_MODE_STATE_BACKEND = "maintenance_mode.backends.CacheBackend"
MAINTENANCE_MODE_STATE_BACKEND_FALLBACK_VALUE = True

VITE_DEV_MODE = env.bool(
    "VITE_DEV_MODE", default=DEBUG, help_text="Set to `on` to enable Vite development mode for HMR in the browser"
)
