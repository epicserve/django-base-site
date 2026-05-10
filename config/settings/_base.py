"""
Django settings for config project.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.2/ref/settings/
"""

import contextlib
import re
import socket
from pathlib import Path

from celery.schedules import crontab
from epicenv import Env

env = Env()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

READ_DOT_ENV_FILE = env.bool("READ_DOT_ENV_FILE", default=True)

if READ_DOT_ENV_FILE is True:
    env.read_env(str(BASE_DIR.joinpath(".env")))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool("DEBUG", default=False)

INSTANCE = env("INSTANCE", default="dev")

ALLOWED_HOSTS: list[str] = env.list("ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
# Only honor X-Forwarded-Proto when explicitly opted in. Setting this when the
# app isn't behind a proxy that strips the header lets a client spoof HTTPS
# detection and bypass `secure`-flag cookies / SECURE_SSL_REDIRECT.
if env.bool("SECURE_PROXY_SSL_HEADER", default=False):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
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
    "apps.organizations",
    "apps.teams",
    "apps.notifications",
    "apps.billing",
    "maintenance_mode",
    "allauth",
    "allauth.account",
    "allauth.headless",
    "allauth.mfa",
    "storages",
    "hijack",
]

# DJANGO HIJACK SETTINGS
HIJACK_PERMISSION_CHECK = "apps.base.hijack_permissions.superuser_only"
HIJACK_LOGIN_REDIRECT_URL = "/"
HIJACK_LOGOUT_REDIRECT_URL = "/"

MIDDLEWARE = [
    "allauth.account.middleware.AccountMiddleware",
    "django_alive.middleware.healthcheck_bypass_host_check",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "maintenance_mode.middleware.MaintenanceModeMiddleware",
    "hijack.middleware.HijackUserMiddleware",
    "apps.organizations.middleware.OrganizationMiddleware",
    "apps.accounts.middleware.TimezoneMiddleware",
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
                "apps.organizations.context_processors.organization",
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
        "DATABASE_URL", default="postgres://postgres@postgres/postgres", ssl_require=DB_SSL_REQUIRED
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

DEFAULT_FILE_STORAGE_BACKEND = env("DEFAULT_FILE_STORAGE", default="django.core.files.storage.FileSystemStorage")

STORAGES = {
    "default": {
        "BACKEND": DEFAULT_FILE_STORAGE_BACKEND,
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Media S3 storage settings (used for both MinIO local dev and real S3 in prod).
# These are read by `apps.base.storage.S3MediaStorage` when DEFAULT_FILE_STORAGE is set
# to an s3boto3-based backend.
MEDIA_S3_ACCESS_KEY = env("MEDIA_S3_ACCESS_KEY", default="")
MEDIA_S3_SECRET_KEY = env("MEDIA_S3_SECRET_KEY", default="")
MEDIA_S3_ENDPOINT_URL = env("MEDIA_S3_ENDPOINT_URL", default="")
MEDIA_S3_URL_ENDPOINT_URL = env("MEDIA_S3_URL_ENDPOINT_URL", default="")
MEDIA_S3_BUCKET_NAME = env("MEDIA_S3_BUCKET_NAME", default="")

if "s3boto3" in DEFAULT_FILE_STORAGE_BACKEND.lower():
    STORAGES["default"]["OPTIONS"] = {
        "access_key": MEDIA_S3_ACCESS_KEY,
        "secret_key": MEDIA_S3_SECRET_KEY,
        "bucket_name": MEDIA_S3_BUCKET_NAME,
        "default_acl": "private",
        "querystring_auth": True,
        "file_overwrite": False,
    }
    if MEDIA_S3_ENDPOINT_URL:
        STORAGES["default"]["OPTIONS"]["endpoint_url"] = MEDIA_S3_ENDPOINT_URL
    if MEDIA_S3_URL_ENDPOINT_URL:
        STORAGES["default"]["BACKEND"] = "apps.base.storage.S3MediaStorage"
        STORAGES["default"]["OPTIONS"]["url_endpoint_url"] = MEDIA_S3_URL_ENDPOINT_URL

# AWS Credentials: Required when using the legacy MediaS3Storage AWS path or Django SES email in non-prod instances
AWS_ACCESS_KEY_ID = env("AWS_ACCESS_KEY_ID", default="")
AWS_SECRET_ACCESS_KEY = env("AWS_SECRET_ACCESS_KEY", default="")


if STORAGES["default"]["BACKEND"].endswith("MediaS3Storage") is True:
    STORAGES["staticfiles"]["BACKEND"] = env("STATICFILES_STORAGE")
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
    PUBLIC_STATIC = PUBLIC_ROOT.joinpath("static")
    STATICFILES_DIRS = [str(PUBLIC_STATIC)]
    MEDIA_URL = "/public/media/"
    STATIC_URL = "/public/static/"

# Tell WhiteNoise that Vite-hashed assets (e.g. app-B7-ckr9u.js, avatar_upload-Cjp3Hco7.css)
# are safe to serve with a long immutable cache, since the hash changes whenever content does.
_VITE_HASHED_ASSET_RE = re.compile(r"-[A-Za-z0-9_-]{8,}\.\w+$")


def _whitenoise_immutable_file_test(path: str, url: str) -> bool:
    return bool(_VITE_HASHED_ASSET_RE.search(url))


WHITENOISE_IMMUTABLE_FILE_TEST = _whitenoise_immutable_file_test

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# CACHE SETTINGS
# Redis scheme docs: https://redis-py.readthedocs.io/en/stable/connections.html#redis.connection.ConnectionPool.from_url
REDIS_URL = env("REDIS_URL", default="redis://redis:6379/0")
REDIS_PREFIX = env("REDIS_PREFIX", default="")
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
CELERY_BEAT_SCHEDULE = {
    "purge-expired-notifications": {
        "task": "apps.notifications.tasks.purge_expired_notifications",
        # Daily at 03:00 UTC. The worker is started with `-B` (embedded beat)
        # in compose.yml; in production use a dedicated beat process.
        "schedule": crontab(hour=3, minute=0),
    },
    # Billing tasks are no-ops when BILLING_ENABLED=False; they remain in the
    # schedule so toggling billing on doesn't require a worker restart.
    "billing-check-trials-ending": {
        "task": "apps.billing.tasks.check_trials_ending",
        "schedule": crontab(hour=4, minute=0),  # daily 04:00 UTC
    },
    "billing-reconcile-subscriptions": {
        "task": "apps.billing.tasks.reconcile_subscriptions",
        "schedule": crontab(day_of_week=1, hour=5, minute=0),  # weekly Mon 05:00 UTC
    },
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"

SITE_ID = 1
SITE_NAME = "Django Base Site"

SITE_DOMAIN = env("SITE_DOMAIN", default="localhost:8000")
SITE_SCHEME = env("SITE_SCHEME", default="http")
SITE_URL = f"{SITE_SCHEME}://{SITE_DOMAIN}"

# Default page size used by the ninja LegacyPagination paginator.
DEFAULT_PAGE_SIZE = 50

# Models registered here get a post_delete receiver that cleans up Notification
# rows whose GenericForeignKey targets them. Add producer-app models as needed.
NOTIFICATIONS_TARGET_MODELS: list[str] = []

# Default retention window for notifications without an explicit `expires_at`.
# The `purge_expired_notifications` celery task / `purge_notifications`
# management command deletes anything older than this.
NOTIFICATIONS_RETENTION_DAYS = env.int("NOTIFICATIONS_RETENTION_DAYS", default=90)

# Notification categories shown on the account-settings Notifications tab and
# consulted by `apps.notifications.categories.should_send`. Use
# `apps.notifications.constants.NotificationChannel` for `default_channels`
# values so typos are caught at import time. Each entry:
#   {
#     "key": "comments",
#     "label": "Comments",
#     "description": "Replies to your posts.",
#     "default_channels": (NotificationChannel.IN_APP, NotificationChannel.EMAIL),
#   }
# Out of the box, no categories are registered. Add entries here as downstream
# apps introduce notification subjects.
NOTIFICATIONS_CATEGORIES: list[dict] = []

# BILLING SETTINGS
# When BILLING_ENABLED is False (the default), the billing API and Stripe
# webhook URL are not mounted, `apps.billing.access.org_has_feature()` returns
# every feature's default, and the SPA hides the pricing page + billing tab.
# This lets the starter template run out of the box without Stripe credentials.
BILLING_ENABLED = env.bool("BILLING_ENABLED", default=False)
STRIPE_SECRET_KEY = env("STRIPE_SECRET_KEY", default="")
STRIPE_PUBLISHABLE_KEY = env("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_WEBHOOK_SECRET = env("STRIPE_WEBHOOK_SECRET", default="")

# Subscription plans. Empty out of the box. See `apps.billing.plans` for the
# expected dict schema. When BILLING_ENABLED is True, `BillingConfig.ready()`
# raises ImproperlyConfigured if a non-free plan has no Stripe price IDs.
BILLING_PLANS: list[dict] = []

# Feature catalog. Empty out of the box. See `apps.billing.features` for the
# expected dict schema. Values from BILLING_PLANS[*]["features"] override
# these defaults at runtime.
BILLING_FEATURES: list[dict] = []

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
# Set to "optional" so users can verify their email. Mailpit captures emails locally during development.
# For production, consider changing to "mandatory".
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_EMAIL_SUBJECT_PREFIX = ""

# CUSTOM Django Base Site ALLAUTH settings used in the custom adapter (apps.accounts.auth_adapter)
ACCOUNT_ADAPTER = "apps.accounts.auth_adapter.AccountAdapter"
ACCOUNT_SIGNUP_OPEN = env.bool("ACCOUNT_SIGNUP_OPEN", default=False)
ACCOUNT_SHOW_POST_LOGIN_MESSAGE = False

# ALLAUTH HEADLESS SETTINGS — with HEADLESS_ONLY=True allauth returns JSON
# instead of rendering templates, and email/redirect links are mapped through
# HEADLESS_FRONTEND_URLS to SPA routes.
HEADLESS_ONLY = True
HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": "/accounts/confirm-email/{key}",
    "account_reset_password_from_key": "/accounts/password/reset/key/{key}",
    "account_signup": "/accounts/signup/",
    "account_login": "/accounts/login/",
    "account_reauthenticate": "/accounts/reauthenticate/",
}

# ALLAUTH MFA SETTINGS
MFA_SUPPORTED_TYPES = ["totp", "recovery_codes", "webauthn"]
MFA_PASSKEY_LOGIN_ENABLED = True
MFA_PASSKEY_SIGNUP_ENABLED = False
MFA_TOTP_ISSUER = SITE_NAME
MFA_RECOVERY_CODE_COUNT = 10

# SPA route paths that legacy Django templates need to link to. These map to
# Vue Router routes defined in frontend/js/router.js; keep them in sync with
# that file. Referenced from templates via the `spa_url` template tag.
SPA_URLS = {
    "account-general": "/accounts/general/",
    "account-email": "/accounts/email/",
    "account-password-change": "/accounts/password/change/",
    "account-security": "/accounts/security/",
    "logout": "/accounts/logout/",
    "org-create": "/organizations/create/",
    "org-switch": "/organizations/switch/",
    "org-settings-general": "/organizations/{slug}/settings/general/",
    "org-settings-members": "/organizations/{slug}/settings/members/",
    "org-settings-teams": "/organizations/{slug}/settings/teams/",
    "impersonate": "/impersonate/",
}

if INSTANCE != "prod":
    # See https://github.com/migonzalvar/dj-email-url for more examples on how to set the EMAIL_URL
    email = env.dj_email_url(
        "EMAIL_URL",
        default="smtp://mailpit:1025",
    )
    DEFAULT_FROM_EMAIL = email.get("DEFAULT_FROM_EMAIL", "webmaster@localhost")
    EMAIL_HOST = email["EMAIL_HOST"]
    EMAIL_PORT = email["EMAIL_PORT"]
    EMAIL_HOST_PASSWORD = email["EMAIL_HOST_PASSWORD"]
    EMAIL_HOST_USER = email["EMAIL_HOST_USER"]
    EMAIL_USE_TLS = email["EMAIL_USE_TLS"]
else:
    # Use Django SES as the email backend for the production instance
    DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="")
    EMAIL_BACKEND = "django_ses.SESBackend"


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
IS_DEBUG_LOGGING_ON = env.bool("IS_DEBUG_LOGGING_ON", default=False)
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

    LOGGING["formatters"]["default"]["class"] = "readable_log_formatter.ReadableFormatter"

# MAINTENANCE MODE SETTINGS
MAINTENANCE_MODE_STATE_BACKEND = "maintenance_mode.backends.CacheBackend"
MAINTENANCE_MODE_STATE_BACKEND_FALLBACK_VALUE = True

VITE_DEV_MODE = env.bool("VITE_DEV_MODE", default=DEBUG)
