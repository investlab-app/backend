import django

from config.containers import setup_container
from config.logging import setup_logging

django.setup()

setup_logging()

container = setup_container()
