from django.conf import settings
from polygon import RESTClient

client = RESTClient(settings.POLYGON_SECRET_KEY)
exchange = "XNAS"
asset_type = "stocks"
