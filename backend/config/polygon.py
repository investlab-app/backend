from django.conf import settings
from polygon import RESTClient, WebSocketClient
from polygon.websocket.models import Feed, Market

client = RESTClient(settings.POLYGON_SECRET_KEY)
exchange = "XNAS"
asset_type = "stocks"

websocket_client = WebSocketClient(
    api_key=settings.POLYGON_SECRET_KEY, feed=Feed.Delayed, market=Market.Stocks
)