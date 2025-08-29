from django.conf import settings
from polygon import RESTClient, WebSocketClient
from polygon.websocket.models import Feed, Market

polygon_client = RESTClient(settings.POLYGON_SECRET_KEY)

polygon_websocket_client = WebSocketClient(
    api_key=settings.POLYGON_SECRET_KEY, feed=Feed.Delayed, market=Market.Stocks
)
