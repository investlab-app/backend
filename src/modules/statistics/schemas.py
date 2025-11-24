from decimal import Decimal

from pydantic import BaseModel


class TransactionStats(BaseModel):
    ticker: str | None

    total_buy_volume: Decimal
    total_buy_price: Decimal
    total_sell_volume: Decimal
    total_sell_price: Decimal

    initial_ticker_volume: Decimal
    initial_ticker_price: Decimal
    final_ticker_volume: Decimal
    final_ticker_price: Decimal

    buy_transactions: int
    sell_transactions: int

    gain: Decimal
    gain_percentage: Decimal | None
