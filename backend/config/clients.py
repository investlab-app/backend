from django.conf import settings
from polygon import RESTClient, WebSocketClient
from polygon.websocket.models import Feed, Market
import redis

polygon_client = RESTClient(settings.POLYGON_SECRET_KEY)

polygon_websocket_client = WebSocketClient(
    api_key=settings.POLYGON_SECRET_KEY, feed=Feed.Delayed, market=Market.Stocks
)

redis_client = redis.Redis(host="redis", port=6379)
