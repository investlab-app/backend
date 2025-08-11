import os

import django

from config.logging import setup_logging

setup_logging()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
