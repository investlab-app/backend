from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


class Action:
    pass


@dataclass(frozen=True)
class BuySellAmountAction(Action):
    action: Literal["buy", "sell"]
    amount: Decimal
    ticker: str


@dataclass(frozen=True)
class BuySellPercentAction(Action):
    action: Literal["buy", "sell"]
    percent: Decimal
    ticker: str


@dataclass(frozen=True)
class BuySellForPriceAction(Action):
    action: Literal["buy", "sell"]
    price: Decimal
    ticker: str


@dataclass(frozen=True)
class NotificationAction(Action):
    format: Literal["push", "email"]
    message: str
