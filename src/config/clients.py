import redis
from clerk_backend_api import Clerk
from django.conf import settings
from openai import OpenAI
from polygon import RESTClient, WebSocketClient
from polygon.websocket.models import Feed, Market

clerk_client = Clerk(bearer_auth=settings.CLERK_SECRET_KEY)

polygon_client = RESTClient(settings.POLYGON_SECRET_KEY)

polygon_websocket_client = WebSocketClient(
    api_key=settings.POLYGON_SECRET_KEY, feed=Feed.Delayed, market=Market.Stocks
)

redis_client = redis.Redis(host="redis", port=6379)
openai_client = OpenAI(
    api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_API_URL
)
