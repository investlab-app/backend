from polygon.rest.models.snapshot import TickerSnapshot
from pydantic import BaseModel


class DailySummary(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: float
    volume_weighted_average_price: float


class DailyPriceSummary(BaseModel):
    ticker: str
    current_price: float
    daily_summary: DailySummary
    todays_change: float
    todays_change_percent: float
    last_updated: int

    @classmethod
    def from_snapshot(cls, snapshot: TickerSnapshot) -> "DailyPriceSummary":
        return cls(
            ticker=snapshot.ticker,
            current_price=snapshot.min.close,
            daily_summary=DailySummary(
                open=snapshot.min.open,
                high=snapshot.min.high,
                low=snapshot.min.low,
                close=snapshot.min.close,
                volume=snapshot.day.volume,
                volume_weighted_average_price=snapshot.day.vwap,
            ),
            todays_change=snapshot.todays_change,
            todays_change_percent=snapshot.todays_change_percent,
            last_updated=snapshot.updated,
        )
