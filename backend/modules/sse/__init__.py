import uuid

from pydantic import BaseModel, Field

from modules.prices.services import LivePrices
from modules.sse.serializers import SSERequestSerializer

live_prices = LivePrices()



