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




class NewsThumbnailResolution(BaseModel):
    url: str
    width: int
    height: int
    tag: str

class NewsThumbnail(BaseModel):
    originalUrl: str
    originalWidth: int
    originalHeight: int
    caption: str
    resolutions: list[NewsThumbnailResolution]

class NewsProvider(BaseModel):
    displayName: str
    url: str

class NewsUrl(BaseModel):
    url: str
    site: str | None
    region: str | None
    lang: str | None

class NewsMetadata(BaseModel):
    editorsPick: bool

class NewsPremiumFinance(BaseModel):
    isPremiumNews: bool
    isPremiumFreeNews: bool

class NewsFinance(BaseModel):
    premiumFinance: NewsPremiumFinance

class NewsContent(BaseModel):
    id: str
    contentType: str
    title: str
    description: str
    summary: str
    pubDate: datetime
    displayTime: str
    isHosted: bool
    bypassModal: bool
    previewUrl: str | None
    thumbnail: NewsThumbnail | None
    provider: NewsProvider
    canonicalUrl: NewsUrl
    clickThroughUrl: NewsUrl
    metadata: NewsMetadata
    finance: NewsFinance
    storyline: dict | None

class NewsItem(BaseModel):
    id: str
    content: NewsContent