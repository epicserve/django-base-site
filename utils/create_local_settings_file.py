from django.utils.crypto import get_random_string
from django.conf import settings
import os

LOCAL_DEV_TEMPLATE = """from .dev import *

LOCAL_SETTINGS_LOADED = True

SECRET_KEY = '<SECRET_KEY>'
"""

if __name__ == '__main__':

    SECRET_KEY_CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    SECRET_KEY = get_random_string(50, SECRET_KEY_CHARS)
    LOCAL_DEV_TEMPLATE = LOCAL_DEV_TEMPLATE.replace('<SECRET_KEY>', SECRET_KEY)
    TARGET_SETTINGS_FILE = os.path.join(settings.BASE_DIR, 'config', 'settings', 'local.py')

    if not os.path.exists(TARGET_SETTINGS_FILE):
        with open(TARGET_SETTINGS_FILE, 'w') as f:
            f.write(LOCAL_DEV_TEMPLATE)
            f.close()
