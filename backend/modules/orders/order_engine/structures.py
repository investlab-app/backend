from dataclasses import dataclass, field
from typing import Optional

@dataclass(eq=True)
class EngineOrder:
    id :str
    ticker :str
    investor_id :str

    def __hash__(self):
        return hash(self.id)


@dataclass(eq=True)
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
    prices :list[dict[str, float]]
    balances :dict[str, float]

@dataclass
class TradeEngineOutput:
    transactions: list[Transaction]
    updated_orders: list[str]
    completed_orders: list[str]