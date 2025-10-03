import uuid
from decimal import Decimal

from pydantic import BaseModel


class EngineOrder(BaseModel):
    id: uuid.UUID
    ticker: str
    investor_id: str


class MarketEngineOrder(EngineOrder):
    volume: Decimal
    is_buy: bool
    volume_processed: Decimal = Decimal(0)


class EngineOrderUpdate(BaseModel):
    id: uuid.UUID


class MarketEngineOrderUpdate(EngineOrderUpdate):
    volume_processed: Decimal


class EngineAsset(BaseModel):
    investor_id: str
    volume: Decimal
    ticker: str


class EngineTransaction(BaseModel):
    ticker: str
    volume: Decimal
    is_buy: bool
    investor_id: str | None = None


class TradeEngineInput(BaseModel):
    orders: list[EngineOrder]
    assets: list[EngineAsset]
    prices: dict[str, Decimal]
    balances: dict[str, Decimal]


class TradeEngineOutput(BaseModel):
    transactions: list[EngineTransaction]
    updated_orders: list[EngineOrderUpdate]
    completed_orders: list[uuid.UUID]
