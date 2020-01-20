import sys
from urllib.parse import urlparse

import environs

env = environs.Env()

BASE_DIR = environs.Path(__file__).parent.parent  # type: ignore

READ_DOT_ENV_FILE = env.bool("READ_DOT_ENV_FILE", default=True)

if READ_DOT_ENV_FILE is True:
    env.read_env(str(BASE_DIR.joinpath(".env")))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
INTERNAL_IPS = env.list("INTERNAL_IPS", default=["127.0.0.1"])

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.base",
    "apps.accounts",
    "allauth",
    "allauth.account",
    "crispy_forms",
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
            ]
        },
    }
]

WSGI_APPLICATION = env("WSGI_APPLICATION", default="config.wsgi.application")

# Database
# See https://github.com/jacobian/dj-database-url for more examples
DATABASES = {
    "default": env.dj_db_url(
        "DATABASE_URL", default=f'sqlite:///{BASE_DIR.joinpath("db.sqlite")}', ssl_require=not DEBUG
    )
}

# Custom User Model
# https://docs.djangoproject.com/en/2.1/topics/auth/customizing/#substituting-a-custom-user-model
AUTH_USER_MODEL = "accounts.User"

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

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
    public_root = BASE_DIR.joinpath("public")
    MEDIA_ROOT = str(public_root.joinpath("media"))
    STATICFILES_DIRS = [str(BASE_DIR.joinpath("public", "static"))]
    MEDIA_URL = "/public/media/"
    STATIC_URL = "/public/static/"

# CACHE SETTINGS
REDIS_HOST = env("REDIS_HOST", default="redis")
REDIS_PORT = env.int("REDIS_PORT", 6379)
REDIS_DB = env.int("REDIS_DB", default=0)
REDIS_PASSWORD = env("REDIS_PASSWORD", default="")
REDISCLOUD_URL = env("REDISCLOUD_URL", default="")

if REDISCLOUD_URL:
    redis_url = urlparse(REDISCLOUD_URL)
    REDIS_HOST = redis_url.hostname
    REDIS_PORT = redis_url.port
    REDIS_PASSWORD = redis_url.password

CACHES = {
    "default": {
        "BACKEND": "redis_cache.RedisCache",
        "LOCATION": f"{REDIS_HOST}:{REDIS_PORT}",
        "OPTIONS": {
            "DB": REDIS_DB,
            "PASSWORD": REDIS_PASSWORD,
            "PARSER_CLASS": "redis.connection.HiredisParser",
            "CONNECTION_POOL_CLASS": "redis.BlockingConnectionPool",
            "CONNECTION_POOL_CLASS_KWARGS": {"max_connections": 50, "timeout": 20},
        },
    }
}

# CRISPY-FORMS
CRISPY_TEMPLATE_PACK = "bootstrap4"

# CELERY SETTINGS
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
if REDISCLOUD_URL:
    CELERY_BROKER_URL = REDISCLOUD_URL

SESSION_ENGINE = "redis_sessions.session"
SESSION_REDIS = {
    "host": REDIS_HOST,
    "port": REDIS_PORT,
    "db": REDIS_DB,
    "password": REDIS_PASSWORD,
    "socket_timeout": 20,
}

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
# SMTP Example: EMAIL_URL='smtp://username:password@smtp.example.com:587/?ssl=True&_default_from_email=John%20Example%20%3Cjohn%40example.com%3E'
email = env.dj_email_url("EMAIL_URL", default="smtp://")
DEFAULT_FROM_EMAIL = email["DEFAULT_FROM_EMAIL"]
EMAIL_HOST = email["EMAIL_HOST"]
EMAIL_PORT = email["EMAIL_PORT"]
EMAIL_HOST_PASSWORD = email["EMAIL_HOST_PASSWORD"]
EMAIL_HOST_USER = email["EMAIL_HOST_USER"]
EMAIL_USE_TLS = email["EMAIL_USE_TLS"]

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

if "test" in sys.argv:

    PASSWORD_HASHERS = (
        "django.contrib.auth.hashers.MD5PasswordHasher",
        "django.contrib.auth.hashers.SHA1PasswordHasher",
    )

    AUTHENTICATION_BACKENDS = ("django.contrib.auth.backends.ModelBackend",)

    DATABASES["default"] = {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}
