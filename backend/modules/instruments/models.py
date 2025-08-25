from dataclasses import dataclass
from typing import TypedDict

from django.db import models
from django.utils.translation import gettext_lazy as _

from modules.core.models import BaseModel
from modules.instruments.constants import LocaleChoices, MarketChoices


class AddressDict(TypedDict):
    address1: str | None
    address2: str | None
    city: str | None
    state: str | None
    postal_code: str | None


class Instrument(BaseModel):
    """Model stores information about an instrument retrieved from the Polygon API."""

    # Polygon Ticker Fields
    active = models.BooleanField(
        verbose_name=_("Active"),
        help_text=_("Indicates whether the ticker is actively traded."),
    )
    cik = models.CharField(
        verbose_name=_("CIK"),
        help_text=_("Central Index Key assigned by the SEC."),
        max_length=20,
        blank=True,
        null=True,
    )
    composite_figi = models.CharField(
        verbose_name=_("Composite FIGI"),
        help_text=_("Composite Financial Instrument Global Identifier."),
        max_length=20,
        blank=True,
        null=True,
    )
    currency_name = models.CharField(
        verbose_name=_("Currency Name"),
        max_length=50,
    )
    currency_symbol = models.CharField(
        verbose_name=_("Currency Symbol"),
        max_length=10,
        blank=True,
        null=True,
    )
    base_currency_symbol = models.CharField(
        verbose_name=_("Base Currency Symbol"),
        help_text=_("Symbol of the base currency for FX or crypto tickers."),
        max_length=10,
        blank=True,
        null=True,
    )
    base_currency_name = models.CharField(
        verbose_name=_("Base Currency Name"),
        help_text=_("Name of the base currency for FX or crypto tickers."),
        max_length=50,
        blank=True,
        null=True,
    )
    locale = models.CharField(
        verbose_name=_("Locale"),
        help_text=_("Locale where the ticker is traded, e.g. 'US'."),
        max_length=10,
        choices=LocaleChoices.choices,
    )
    market = models.CharField(
        verbose_name=_("Market"),
        max_length=20,
        choices=MarketChoices.choices,
    )
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=255,
    )
    primary_exchange = models.CharField(
        verbose_name=_("Primary Exchange"),
        help_text=_("Code of the primary exchange where the ticker is traded."),
        max_length=50,
        blank=True,
        null=True,
    )
    share_class_figi = models.CharField(
        verbose_name=_("Share Class FIGI"),
        max_length=20,
        blank=True,
        null=True,
    )
    ticker = models.CharField(
        verbose_name=_("Ticker Symbol"),
        max_length=20,
        unique=True,
        db_index=True,
    )
    type = models.CharField(
        verbose_name=_("Type"),
        help_text=_("Security type, e.g. 'CS' (Common Stock), 'ETF', 'Crypto'."),
        max_length=50,
        blank=True,
        null=True,
    )

    # Polygon TickerDetails Fields
    description = models.TextField(
        verbose_name=_("Description"),
        blank=True,
        null=True,
    )
    ticker_root = models.CharField(
        verbose_name=_("Ticker Root"),
        help_text=_("Base symbol for related tickers."),
        max_length=50,
        blank=True,
        null=True,
    )
    ticker_suffix = models.CharField(
        verbose_name=_("Ticker Suffix"),
        help_text=_("Suffix for ticker if applicable."),
        max_length=50,
        blank=True,
        null=True,
    )
    homepage_url = models.URLField(
        verbose_name=_("Homepage URL"),
        blank=True,
        null=True,
    )
    list_date = models.DateField(
        verbose_name=_("List Date"),
        help_text=_("Date when the ticker was first listed."),
        blank=True,
        null=True,
    )
    market_cap = models.DecimalField(
        verbose_name=_("Market Cap"),
        max_digits=20,
        decimal_places=2,
        blank=True,
        null=True,
    )
    phone_number = models.CharField(
        verbose_name=_("Phone Number"),
        max_length=30,
        blank=True,
        null=True,
    )
    share_class_shares_outstanding = models.BigIntegerField(
        verbose_name=_("Shares Outstanding (Share Class)"),
        help_text=_("Number of shares outstanding for this share class."),
        blank=True,
        null=True,
    )
    sic_code = models.CharField(
        verbose_name=_("SIC Code"),
        help_text=_("Standard Industrial Classification code."),
        max_length=10,
        blank=True,
        null=True,
    )
    sic_description = models.CharField(
        verbose_name=_("SIC Description"),
        max_length=255,
        blank=True,
        null=True,
    )
    total_employees = models.IntegerField(
        verbose_name=_("Total Employees"),
        blank=True,
        null=True,
    )
    weighted_shares_outstanding = models.BigIntegerField(
        verbose_name=_("Weighted Shares Outstanding"),
        blank=True,
        null=True,
    )

    # Polygon CompanyAddress fields
    address1 = models.CharField(
        verbose_name=_("Address Line 1"),
        max_length=255,
        blank=True,
        null=True,
    )
    address2 = models.CharField(
        verbose_name=_("Address Line 2"),
        max_length=255,
        blank=True,
        null=True,
    )
    city = models.CharField(
        verbose_name=_("City"),
        max_length=100,
        blank=True,
        null=True,
    )
    state = models.CharField(
        verbose_name=_("State"),
        max_length=100,
        blank=True,
        null=True,
    )
    country = models.CharField(
        verbose_name=_("Country"),
        max_length=100,
        blank=True,
        null=True,
    )
    postal_code = models.CharField(
        verbose_name=_("Postal Code"),
        max_length=20,
        blank=True,
        null=True,
    )

    # Polygon Branding fields
    icon_url = models.URLField(
        verbose_name=_("Icon URL"),
        blank=True,
        null=True,
    )
    logo_url = models.URLField(
        verbose_name=_("Logo URL"),
        blank=True,
        null=True,
    )

    @property
    def address(self) -> AddressDict:
        return AddressDict(
            address1=self.address1,
            address2=self.address2,
            city=self.city,
            state=self.state,
            postal_code=self.postal_code,
        )

    class Meta:
        verbose_name = _("Instrument")
        verbose_name_plural = _("Instruments")
        ordering = ["ticker"]

    def __str__(self):
        return f"{self.ticker} - {self.name or _('Unnamed')}"
