from pydantic import BaseModel


class DailySummary(BaseModel):
    open: float
    high: float
    low: float
    close: float
    volume: float
    volume_weighted_average_price: float


class DailyPriceSummary(BaseModel):
    current_price: float
    daily_summary: DailySummary
    todays_change: float
    todays_change_percent: float
    last_updated: int
