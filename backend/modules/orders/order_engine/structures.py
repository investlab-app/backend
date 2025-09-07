from decimal import Decimal

from pydantic import BaseModel


class EngineOrder(BaseModel):
    id: str
    ticker: str
    investor_id: int


class MarketEngineOrder(EngineOrder):
    volume: Decimal
    is_buy: bool
    volume_processed: Decimal = 0


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
    updated_orders: list[EngineOrder]
    completed_orders: list[EngineOrder]
