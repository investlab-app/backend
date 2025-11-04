from django.conf import settings
from openai import OpenAI
from polygon import RESTClient, WebSocketClient
from polygon.websocket.models import Feed, Market
from pydantic_ai.providers.google import GoogleProvider
from pydantic_ai.providers.groq import GroqProvider
from pydantic_ai.providers.openai import OpenAIProvider

polygon_client = RESTClient(settings.POLYGON_SECRET_KEY)

polygon_websocket_client = WebSocketClient(
    api_key=settings.POLYGON_SECRET_KEY, feed=Feed.Delayed, market=Market.Stocks
)

openai_client = OpenAI(api_key=settings.GROQ_API_KEY)

groq_provider = GroqProvider(
    api_key=settings.GROQ_API_KEY,
)
openai_provider = OpenAIProvider(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY,
)
gemini_provider = GoogleProvider(
    api_key=settings.GEMINI_API_KEY,
)
