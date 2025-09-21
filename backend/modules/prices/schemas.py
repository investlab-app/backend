from decimal import Decimal

from polygon.rest.models.snapshot import TickerSnapshot
from pydantic import BaseModel

from modules.core.utils import to_quantized_decimal


class DailySummary(BaseModel):
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    volume_weighted_average_price: Decimal


class DailyPriceSummary(BaseModel):
    ticker: str
    current_price: Decimal
    daily_summary: DailySummary
    todays_change: Decimal
    todays_change_percent: Decimal
    last_updated: int

    @classmethod
    def from_snapshot(cls, snapshot: TickerSnapshot) -> "DailyPriceSummary":
        return cls(
            ticker=snapshot.ticker,
            current_price=to_quantized_decimal(snapshot.min.close),
            daily_summary=DailySummary(
                open=to_quantized_decimal(snapshot.min.open),
                high=to_quantized_decimal(snapshot.min.high),
                low=to_quantized_decimal(snapshot.min.low),
                close=to_quantized_decimal(snapshot.min.close),
                volume=to_quantized_decimal(snapshot.day.volume),
                volume_weighted_average_price=to_quantized_decimal(snapshot.day.vwap),
            ),
            todays_change=to_quantized_decimal(snapshot.todays_change),
            todays_change_percent=to_quantized_decimal(snapshot.todays_change_percent),
            last_updated=snapshot.updated,
        )
