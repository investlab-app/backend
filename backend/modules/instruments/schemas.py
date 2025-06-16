from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class InstrumentBasicInfoSchema(BaseModel):
    """Basic information about an instrument, suitable for table views."""

    ticker: str | None = None
    name: str | None = None
    currency: str | None = None
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


class NewsThumbnailResolution(BaseModel):
    url: str | None = None
    width: int | None = None
    height: int | None = None
    tag: str | None = None


class NewsThumbnail(BaseModel):
    original_url: str | None = None
    original_width: int | None = None
    original_height: int | None = None
    caption: str | None = None
    resolutions: list[NewsThumbnailResolution] | None = None


class NewsProvider(BaseModel):
    display_name: str | None = None
    url: str | None = None


class NewsUrl(BaseModel):
    url: str | None = None
    site: str | None = None
    region: str | None = None
    lang: str | None = None


class NewsMetadata(BaseModel):
    editors_pick: bool | None = None


class NewsPremiumFinance(BaseModel):
    is_premium_news: bool | None = None
    is_premium_free_news: bool | None = None


class NewsFinance(BaseModel):
    premium_finance: NewsPremiumFinance | None = None


class NewsContent(BaseModel):
    id: str | None = None
    content_type: str | None = None
    title: str | None = None
    description: str | None = None
    summary: str | None = None
    pub_date: datetime | None = None
    display_time: str | None = None
    is_hosted: bool | None = None
    bypass_modal: bool | None = None
    preview_url: str | None = None
    thumbnail: NewsThumbnail | None = None
    provider: NewsProvider | None = None
    canonical_url: NewsUrl | None = None
    click_through_url: NewsUrl | None = None
    metadata: NewsMetadata | None = None
    finance: NewsFinance | None = None
    storyline: dict | None = None


class NewsItem(BaseModel):
    id: str | None = None
    content: NewsContent | None = None
