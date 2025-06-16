import django

from config.containers import setup_container
from config.logging import setup_logging

setup_logging()

django.setup()

container = setup_container()
