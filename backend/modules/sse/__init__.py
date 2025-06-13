import uuid

from pydantic import BaseModel, Field

from modules.prices.services import LivePrices

live_prices = LivePrices()
