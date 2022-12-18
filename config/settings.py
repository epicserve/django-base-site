import socket
import sys

import environs

env = environs.Env()

"""
Django settings for config project.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""

BASE_DIR = environs.Path(__file__).parent.parent  # type: ignore

READ_DOT_ENV_FILE = env.bool("READ_DOT_ENV_FILE", default=True)

if READ_DOT_ENV_FILE is True:
    env.read_env(str(BASE_DIR.joinpath(".env")))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
INTERNAL_IPS = env.list("INTERNAL_IPS", default=["127.0.0.1"])

# Get the IP to use for Django Debug Toolbar when developing with docker
if env.bool("USE_DOCKER", default=False) is True:
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

WSGI_APPLICATION = env("WSGI_APPLICATION", default="config.wsgi.application")
DB_SSL_REQUIRED = env.bool("DB_SSL_REQUIRED", default=not DEBUG)

# Database
# See https://github.com/jacobian/dj-database-url for more examples
DATABASES = {
    "default": env.dj_db_url(
        "DATABASE_URL", default=f'sqlite:///{BASE_DIR.joinpath("db.sqlite")}', ssl_require=DB_SSL_REQUIRED
    )
}

# Custom User Model
# https://docs.djangoproject.com/en/4.1/topics/auth/customizing/#substituting-a-custom-user-model
AUTH_USER_MODEL = "accounts.User"

# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True


USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

DEFAULT_FILE_STORAGE = env("DEFAULT_FILE_STORAGE", default="django.core.files.storage.FileSystemStorage")

if DEFAULT_FILE_STORAGE.endswith("MediaS3Storage") is True:
    STATICFILES_STORAGE = env("STATICFILES_STORAGE")
    AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = env("AWS_STORAGE_BUCKET_NAME")
    AWS_DEFAULT_ACL = "public-read"
    AWS_S3_REGION = env("AWS_S3_REGION", default="us-east-2")
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
    PUBLIC_STATIC = BASE_DIR.joinpath("public", "static")
    STATICFILES_DIRS = [PUBLIC_STATIC]
    MEDIA_URL = "/public/media/"
    STATIC_URL = "/public/static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CACHE SETTINGS
CACHE_URL = env("REDIS_URL", default="redis://redis:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": CACHE_URL,
    }
}

# CRISPY-FORMS
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# CELERY SETTINGS
CELERY_BROKER_URL = env("CACHE_URL", CACHE_URL)

SESSION_ENGINE = "django.contrib.sessions.backends.cache"

SITE_ID = 1
SITE_NAME = "Django Base Site"

# DJANGO DEBUG TOOLBAR SETTINGS
if DEBUG is True:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    DEBUG_TOOLBAR_CONFIG = {"INTERCEPT_REDIRECTS": False}

# ALLAUTH SETTINGS
LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"

# See https://github.com/migonzalvar/dj-email-url for more examples on how to set the EMAIL_URL
email = env.dj_email_url(
    "EMAIL_URL",
    default="smtp://skroob@planetspaceball.com:12345@smtp.planetspaceball.com:587/?ssl=True&_default_from_email=President%20Skroob%20%3Cskroob@planetspaceball.com%3E",
)
DEFAULT_FROM_EMAIL = email["DEFAULT_FROM_EMAIL"]
EMAIL_HOST = email["EMAIL_HOST"]
EMAIL_PORT = email["EMAIL_PORT"]
EMAIL_HOST_PASSWORD = email["EMAIL_HOST_PASSWORD"]
EMAIL_HOST_USER = email["EMAIL_HOST_USER"]
EMAIL_USE_TLS = email["EMAIL_USE_TLS"]

if "test" in sys.argv:

    PASSWORD_HASHERS = (
        "django.contrib.auth.hashers.MD5PasswordHasher",
        "django.contrib.auth.hashers.SHA1PasswordHasher",
    )

    AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

    DATABASES["default"] = {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
