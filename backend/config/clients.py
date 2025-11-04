from django.conf import settings
from openai import OpenAI
from polygon import RESTClient, WebSocketClient
from polygon.websocket.models import Feed, Market
from pydantic_ai.providers.openai import OpenAIProvider

polygon_client = RESTClient(settings.POLYGON_SECRET_KEY)

polygon_websocket_client = WebSocketClient(
    api_key=settings.POLYGON_SECRET_KEY, feed=Feed.Delayed, market=Market.Stocks
)

openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

openai_provider = OpenAIProvider(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENAI_API_KEY,
)
