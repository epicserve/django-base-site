from base import *


try:
    SETTINGS_LOCAL
except NameError:
    try:
        from local import *
    except ImportError:
        pass