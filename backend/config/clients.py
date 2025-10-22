from django.conf import settings
from openai import OpenAI
from polygon import RESTClient, WebSocketClient
from polygon.websocket.models import Feed, Market

polygon_client = RESTClient(settings.POLYGON_SECRET_KEY)

polygon_websocket_client = WebSocketClient(
    api_key=settings.POLYGON_SECRET_KEY, feed=Feed.Delayed, market=Market.Stocks
)

openai_client = OpenAI(api_key=settings.GROQ_API_KEY)
