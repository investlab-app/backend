from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

class InstrumentBasicInfoSchema(BaseModel):
    """Basic information about an instrument, suitable for table views."""
    ticker: str
    name: str
    currency: str
    current_price: Decimal | None = None
    previous_close: Decimal | None = None
    day_change: Decimal | None = None
    day_change_percent: Decimal | None = None
    market_cap: Decimal | None = None
    volume: int | None = None
    sector: str | None = None
    industry: str | None = None
    country: str | None = None


class InstrumentDetailedInfoSchema(InstrumentBasicInfoSchema):
    """Detailed information about an instrument, for comprehensive display."""
    description: str | None = None
    website: str | None = None
    logo_url: str | None = None
    exchange: str | None = None
    fifty_two_week_low: Decimal | None = None
    fifty_two_week_high: Decimal | None = None
    trailing_pe: Decimal | None = None
    forward_pe: Decimal | None = None
    dividend_yield: Decimal | None = None
    earnings_date: datetime | None = None
    business_summary: str | None = None
    financial_data: dict | None = None
    major_holders: dict | None = None
    institutional_holders: list[dict] | None = None
    analyst_recommendations: dict | None = None
