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

    def serialize(self) -> dict:
        data = {
            'timestamp': self.timestamp.timestamp(),
            'open': str(self.open),
            'high': str(self.high),
            'low': str(self.low),
            'close': str(self.close),
            'volume': str(self.volume),
        }
        if self.transactions is not None:
            data['transactions'] = self.transactions
        if self.volume_weighted_average_price is not None:
            data['volume_weighted_average_price'] = str(self.volume_weighted_average_price)

        return data

    @classmethod
    def deserialize(cls, data :dict):
        transactions = None
        volume_weighted_average_price = None
        if 'transactions' in data:
            transactions = data['transactions']
        if 'volume_weighted_average_price' in data:
            volume_weighted_average_price = Decimal(data['volume_weighted_average_price'])

        return cls(
            timestamp = datetime.fromtimestamp(data['timestamp']),
            open = Decimal(data['open']),
            high = Decimal(data['high']),
            low = Decimal(data['low']),
            close = Decimal(data['close']),
            volume = Decimal(data['volume']),
            transactions = transactions,
            volume_weighted_average_price = Decimal(volume_weighted_average_price)
        )



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

    @classmethod
    def from_ws(cls, data :dict) -> "PriceBar":
        try:
            open_ = to_quantized_decimal(data['open'])
            high = to_quantized_decimal(data['high'])
            low = to_quantized_decimal(data['low'])
            close = to_quantized_decimal(data['close'])
            volume = to_quantized_decimal(data['volume'])
            timestamp = datetime.fromtimestamp(data['end_timestamp'] // 1000)
            if data['aggregate_vwap'] is not None:
                aggregate_vwap = to_quantized_decimal(data['aggregate_vwap'])
            else:
                aggregate_vwap = None

            return cls(
                timestamp = timestamp,
                open = open_,
                high = high,
                low = low,
                close = close,
                volume = volume,
                volume_weighted_average_price = aggregate_vwap,
                transactions = None
            )
        except Exception as e:
            raise ValueError("Failed to create price bar from ws data") from e


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
