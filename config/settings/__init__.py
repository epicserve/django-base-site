from base import *


try:
    LOCAL_SETTINGS_LOADED
except NameError:
    try:
        from local import *
    except ImportError:
        pass
