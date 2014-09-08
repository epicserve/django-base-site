from .base import *
import sys

DEBUG = True

INTERNAL_IPS = ('127.0.0.1', '10.0.2.2')

# Example Gmail settings if you need to send email from a local Django dev
# site. Uncomment the following and change the username and password to
# whatever they are for your Gmail account. Make sure don't use Gmail for
# sending email on a production website.
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_HOST_USER = 'username@gmail.com'
# EMAIL_HOST_PASSWORD = 'xxxxxxxx'
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True

# ADMINS = (
#     ('Your Name', 'username@example.com'),
# )

MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware', )
INSTALLED_APPS += (
    'debug_toolbar',
)
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

# Test settings
if 'test' in sys.argv:

    SOUTH_TESTS_MIGRATE = False
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:'
    }

    PASSWORD_HASHERS = (
        'django.contrib.auth.hashers.MD5PasswordHasher',
        'django.contrib.auth.hashers.SHA1PasswordHasher',
    )

try:
    LOCAL_SETTINGS_LOADED
except NameError:
    try:
        from .local import *
    except ImportError:
        SECRET_KEY = '<replace-this-with-a-new-random-string-or-put-the-secret-key-in-local-settings>'
