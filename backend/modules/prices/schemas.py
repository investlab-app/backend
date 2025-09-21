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
        if not all([agg.timestamp, agg.open, agg.high, agg.low, agg.close, agg.volume]):
            raise ValueError("Agg object is missing required fields")

        return cls(
            timestamp=datetime.fromtimestamp(agg.timestamp // 1000),  # type: ignore
            open=to_quantized_decimal(agg.open),  # type: ignore
            high=to_quantized_decimal(agg.high),  # type: ignore
            low=to_quantized_decimal(agg.low),  # type: ignore
            close=to_quantized_decimal(agg.close),  # type: ignore
            volume=to_quantized_decimal(agg.volume),  # type: ignore
            transactions=agg.transactions,
            volume_weighted_average_price=to_quantized_decimal(agg.vwap)  # type: ignore
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
    def from_snapshot(cls, snapshot: TickerSnapshot) -> "PriceDailySummary":  # type: ignore
        if not all([
            snapshot.ticker,
            snapshot.min and snapshot.min.close,  # type: ignore
            snapshot.day
            and snapshot.day.open  # type: ignore
            and snapshot.day.high  # type: ignore
            and snapshot.day.low  # type: ignore
            and snapshot.day.close  # type: ignore
            and snapshot.day.volume  # type: ignore
            and snapshot.day.vwap,  # type: ignore
            snapshot.todays_change is not None,
            snapshot.todays_change_percent is not None,
            snapshot.updated,
        ]):
            raise ValueError("TickerSnapshot object is missing required fields")

        return cls(
            ticker=snapshot.ticker,
            current_price=to_quantized_decimal(snapshot.min.close),  # type: ignore
            daily_summary=PriceDaily(
                open=to_quantized_decimal(snapshot.day.open),  # type: ignore
                high=to_quantized_decimal(snapshot.day.high),  # type: ignore
                low=to_quantized_decimal(snapshot.day.low),  # type: ignore
                close=to_quantized_decimal(snapshot.day.close),  # type: ignore
                volume=to_quantized_decimal(snapshot.day.volume),  # type: ignore
                volume_weighted_average_price=to_quantized_decimal(snapshot.day.vwap),  # type: ignore
            ),
            todays_change=to_quantized_decimal(snapshot.todays_change),  # type: ignore
            todays_change_percent=to_quantized_decimal(snapshot.todays_change_percent),  # type: ignore
            last_updated=datetime.fromtimestamp(snapshot.updated // 1e9),  # type: ignore
        )
