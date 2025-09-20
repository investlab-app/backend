import uuid
from decimal import Decimal

from pydantic import BaseModel


class EngineOrder(BaseModel):
    id: uuid.UUID
    ticker: str
    investor_id: int


class MarketEngineOrder(EngineOrder):
    volume: Decimal
    is_buy: bool
    volume_processed: Decimal = 0


class EngineOrderUpdate(BaseModel):
    id: uuid.UUID


class MarketEngineOrderUpdate(EngineOrderUpdate):
    volume_processed: Decimal


class EngineAsset(BaseModel):
    investor_id: int
    volume: Decimal
    ticker: str


class EngineTransaction(BaseModel):
    ticker: str
    volume: Decimal
    is_buy: bool
    investor_id: int | None = None


class TradeEngineInput(BaseModel):
    orders: list[EngineOrder]
    assets: list[EngineAsset]
    prices: dict[str, Decimal]
    balances: dict[int, Decimal]


class TradeEngineOutput(BaseModel):
    transactions: list[EngineTransaction]
    updated_orders: list[EngineOrderUpdate]
    completed_orders: list[uuid.UUID]
