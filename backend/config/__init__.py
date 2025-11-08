import os

import django

from config.celery import app as celery_app
from config.logging import setup_logging

__all__ = ("celery_app",)

setup_logging()

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
