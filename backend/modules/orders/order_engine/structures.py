from dataclasses import dataclass
from typing import Optional
from decimal import Decimal

@dataclass
class EngineOrder:
    id :str
    ticker :str
    investor_id :str


@dataclass
class MarketEngineOrder(EngineOrder):
    volume :int
    is_buy :bool
    volume_processed :int = 0

@dataclass
class EngineAsset:
    investor_id :str
    volume :int
    ticker :str

@dataclass
class Transaction:
    ticker: str
    volume: int
    is_buy: bool
    investor_id: Optional[str] = None

@dataclass
class TradeEngineInput:
    orders :list[EngineOrder]
    assets :list[EngineAsset]
    prices :list[dict[str, Decimal]]
    balances :dict[str, Decimal]

@dataclass
class TradeEngineOutput:
    transactions: list[Transaction]
    updated_orders: list[EngineOrder]
    completed_orders: list[EngineOrder]