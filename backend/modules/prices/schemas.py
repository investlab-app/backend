from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from polygon.rest.models.snapshot import Agg, TickerSnapshot

from modules.core.utils import to_quantized_decimal


@dataclass
class PriceBar:
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    transactions: int | None = None
    volume_weighted_average_price: Decimal | None = None

    @classmethod
    def from_agg(cls, agg: Agg) -> "PriceBar":
        if (
            agg.timestamp is None
            or agg.open is None
            or agg.high is None
            or agg.low is None
            or agg.close is None
            or agg.volume is None
        ):
            raise ValueError("Agg object is missing required fields")

        return cls(
            timestamp=datetime.fromtimestamp(agg.timestamp // 1000),
            open=to_quantized_decimal(agg.open),
            high=to_quantized_decimal(agg.high),
            low=to_quantized_decimal(agg.low),
            close=to_quantized_decimal(agg.close),
            volume=to_quantized_decimal(agg.volume),
            transactions=agg.transactions,
            volume_weighted_average_price=to_quantized_decimal(agg.vwap)
            if agg.vwap is not None
            else None,
        )


@dataclass
class PriceDaily:
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    volume_weighted_average_price: Decimal


@dataclass
class PriceDailySummary:
    ticker: str
    current_price: Decimal
    daily_summary: PriceDaily
    todays_change: Decimal
    todays_change_percent: Decimal
    last_updated: datetime

    @classmethod
    def from_snapshot(cls, snapshot: TickerSnapshot) -> "PriceDailySummary":
        if (
            snapshot.ticker is None
            or snapshot.min is None
            or snapshot.min.close is None
            or snapshot.day is None
            or snapshot.day.open is None
            or snapshot.day.high is None
            or snapshot.day.low is None
            or snapshot.day.close is None
            or snapshot.day.volume is None
            or snapshot.day.vwap is None
            or snapshot.todays_change is None
            or snapshot.todays_change_percent is None
            or snapshot.updated is None
        ):
            raise ValueError("TickerSnapshot object is missing required fields")

        return cls(
            ticker=snapshot.ticker,
            current_price=to_quantized_decimal(snapshot.min.close),
            daily_summary=PriceDaily(
                open=to_quantized_decimal(snapshot.day.open),
                high=to_quantized_decimal(snapshot.day.high),
                low=to_quantized_decimal(snapshot.day.low),
                close=to_quantized_decimal(snapshot.day.close),
                volume=to_quantized_decimal(snapshot.day.volume),
                volume_weighted_average_price=to_quantized_decimal(snapshot.day.vwap),
            ),
            todays_change=to_quantized_decimal(snapshot.todays_change),
            todays_change_percent=to_quantized_decimal(snapshot.todays_change_percent),
            last_updated=datetime.fromtimestamp(snapshot.updated // 1e9),
        )
