#!/usr/bin/env python
import os

from django.core.management.color import make_style

os.environ.setdefault("WRITE_DOT_ENV_FILE", "True")

from config import settings  # noqa: E402

style = make_style()

settings.env.write_env_file()
print(style.SUCCESS("Successfully created initial env file!"))
