import os

import django

from config.logging import setup_logging

setup_logging()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from config.containers import AppContainer  # noqa: E402 I001

container = AppContainer()
