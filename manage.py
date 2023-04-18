#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main() -> None:
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

    from django.conf import settings

    if (
        settings.DEBUG
        and os.environ.get("PYCHARM_HOSTED") != "1"
        and os.environ.get("RUN_MAIN")
        or os.environ.get("WERKZEUG_RUN_MAIN")
    ):
        import debugpy

        # Use "nosec" inline comment to ignore security check because this doesn't run in production
        debugpy.listen(("0.0.0.0", 5678))  # nosec
        print("Debugpy attached!")

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
