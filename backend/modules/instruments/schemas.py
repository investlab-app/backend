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
    originalUrl: str | None = None
    originalWidth: int | None = None
    originalHeight: int | None = None
    caption: str | None = None
    resolutions: list[NewsThumbnailResolution] | None = None


class NewsProvider(BaseModel):
    displayName: str | None = None
    url: str | None = None


class NewsUrl(BaseModel):
    url: str | None = None
    site: str | None = None
    region: str | None = None
    lang: str | None = None


class NewsMetadata(BaseModel):
    editorsPick: bool | None = None


class NewsPremiumFinance(BaseModel):
    isPremiumNews: bool | None = None
    isPremiumFreeNews: bool | None = None


class NewsFinance(BaseModel):
    premiumFinance: NewsPremiumFinance | None = None


class NewsContent(BaseModel):
    id: str | None = None
    contentType: str | None = None
    title: str | None = None
    description: str | None = None
    summary: str | None = None
    pubDate: datetime | None = None
    displayTime: str | None = None
    isHosted: bool | None = None
    bypassModal: bool | None = None
    previewUrl: str | None = None
    thumbnail: NewsThumbnail | None = None
    provider: NewsProvider | None = None
    canonicalUrl: NewsUrl | None = None
    clickThroughUrl: NewsUrl | None = None
    metadata: NewsMetadata | None = None
    finance: NewsFinance | None = None
    storyline: dict | None = None


class NewsItem(BaseModel):
    id: str | None = None
    content: NewsContent | None = None
