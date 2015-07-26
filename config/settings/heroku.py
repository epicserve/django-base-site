from .base import *
import dj_database_url

DEBUG = False

COMPRESS_ENABLED = False

# Parse database configuration from $DATABASE_URL
DATABASES['default'] = dj_database_url.config(default=os.environ['DATABASE_URL'])

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Allow all host headers
ALLOWED_HOSTS = ['*']

# Static asset configuration
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

SECRET_KEY = os.environ['SECRET_KEY']
