from django.conf import settings
from polygon import RESTClient

polygon_client = RESTClient(settings.POLYGON_SECRET_KEY)
