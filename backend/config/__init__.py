import os

import django

from config.containers import setup_container
from config.logging import setup_logging

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

setup_logging()
container = setup_container()
