import base64
import os
import socket

import environs
from config.env_writer import EnvWriter

"""
Django settings for config project.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

BASE_DIR = environs.Path(__file__).parent.parent.parent  # type: ignore

env = EnvWriter(base_dir=BASE_DIR, read_dot_env_file=False)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env(
    "SECRET_KEY",
    initial=lambda: base64.b64encode(os.urandom(60)).decode(),
    help_text="Django's SECRET_KEY used to provide cryptographic signing.",
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=True, help_text="Set Django Debug mode to on or off")

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS", default=["127.0.0.1"], help_text="List of allowed hosts that this Django site can serve"
)
INTERNAL_IPS = env.list("INTERNAL_IPS", default=["127.0.0.1"], help_text="IPs allowed to run in debug mode")

# Get the IP to use for Django Debug Toolbar when developing with docker
if env.bool("USE_DOCKER", default=True, help_text="Used to set add the IP to INTERNAL_IPS for Docker Compose") is True:
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
    "allauth",
    "allauth.account",
    "crispy_forms",
    "crispy_bootstrap5",
    "storages",
]

MIDDLEWARE = [
    "allauth.account.middleware.AccountMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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
                "apps.base.context_processors.site_name",
            ],
        },
    },
]

WSGI_APPLICATION = env("WSGI_APPLICATION", default="config.wsgi.application", help_text="WSGI application to use")

# Database
# See https://github.com/jacobian/dj-database-url for more examples
DATABASES = {
    "default": env.dj_db_url(
        "DATABASE_URL",
        default="postgres://postgres:@db:5432/postgres",
        help_text="Database URL for connecting to database",
    )
}

# Custom User Model
# https://docs.djangoproject.com/en/4.2/topics/auth/customizing/#substituting-a-custom-user-model
AUTH_USER_MODEL = "accounts.User"

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True


USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

STORAGES = {
    "default": {
        "BACKEND": env(
            "DEFAULT_FILE_STORAGE",
            default="django.core.files.storage.FileSystemStorage",
            help_text="Default storage backend for media files",
        ),
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


if STORAGES["default"]["BACKEND"].endswith("MediaS3Storage") is True:
    STORAGES["staticfiles"]["BACKEND"] = env("STATICFILES_STORAGE")
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", help_text="AWS Access Key ID if using S3 storage backend")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", help_text="AWS Secret Access Key if using S3 storage backend")
    AWS_STORAGE_BUCKET_NAME = env(
        "AWS_STORAGE_BUCKET_NAME", help_text="AWS Storage Bucket Name if using S3 storage backend"
    )
    AWS_DEFAULT_ACL = "public-read"
    AWS_S3_REGION = env("AWS_S3_REGION", default="us-east-2", help_text="AWS S3 Region if using S3 storage backend")
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
    STATICFILES_DIRS = [PUBLIC_STATIC]
    MEDIA_URL = "/public/media/"
    STATIC_URL = "/public/static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CACHE SETTINGS
REDIS_URL = env("REDIS_URL", default="redis://redis:6379/0", help_text="Redis URL for connecting to redis")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# CRISPY-FORMS
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# CELERY SETTINGS
CELERY_BROKER_URL = REDIS_URL

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
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
# This is set to "none" so when trying out an app idea you don't have to have sending emails setup, which can be a pain.
# It's not recommended to leave it as none on a production system. Choose either mandatory or optional.
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False

# CUSTOM Django Base Site ALLAUTH settings used in the custom adapter (apps.accounts.auth_adapter)
ACCOUNT_ADAPTER = "apps.accounts.auth_adapter.AccountAdapter"
ACCOUNT_SIGNUP_OPEN = False
ACCOUNT_SHOW_POST_LOGIN_MESSAGE = False

# See https://github.com/migonzalvar/dj-email-url for more examples on how to set the EMAIL_URL
email = env.dj_email_url(
    "EMAIL_URL",
    default="smtp://skroob@planetspaceball.com:12345@smtp.planetspaceball.com:587/?ssl=True&_default_from_email=President%20Skroob%20%3Cskroob@planetspaceball.com%3E",
    help_text="URL used for setting Django's email settings",
)
DEFAULT_FROM_EMAIL = email["DEFAULT_FROM_EMAIL"]
EMAIL_HOST = email["EMAIL_HOST"]
EMAIL_PORT = email["EMAIL_PORT"]
EMAIL_HOST_PASSWORD = email["EMAIL_HOST_PASSWORD"]
EMAIL_HOST_USER = email["EMAIL_HOST_USER"]
EMAIL_USE_TLS = email["EMAIL_USE_TLS"]
