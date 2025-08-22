from django.db import models
from django.utils.translation import gettext_lazy as _

from modules.core.models import BaseModel
from modules.instruments_v3.constants import LocaleChoices, MarketChoices


class Ticker(BaseModel):
    """Model stores information about a stock ticker retrieved from the Polygon API."""

    # Polygon Fields
    active = models.BooleanField(
        verbose_name=_("Active"),
        help_text=_("Indicates whether the ticker is actively traded."),
        blank=True,
        null=True,
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
        help_text=_("Full name of the currency."),
        max_length=50,
        blank=True,
        null=True,
    )
    currency_symbol = models.CharField(
        verbose_name=_("Currency Symbol"),
        help_text=_("Currency ISO symbol."),
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
    delisted_utc = models.DateTimeField(
        verbose_name=_("Delisted Date (UTC)"),
        help_text=_("The date and time when the ticker was delisted."),
        blank=True,
        null=True,
    )
    last_updated_utc = models.DateTimeField(
        verbose_name=_("Last Updated (UTC)"),
        help_text=_("The date and time when the ticker data was last updated."),
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
        help_text=_("Market type, e.g. 'stocks', 'crypto', 'fx'."),
        max_length=20,
        choices=MarketChoices.choices,
    )
    name = models.CharField(
        verbose_name=_("Company Name"),
        help_text=_("Full name of the company or instrument."),
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
        help_text=_("Share class-specific FIGI."),
        max_length=20,
        blank=True,
        null=True,
    )
    ticker = models.CharField(
        verbose_name=_("Ticker Symbol"),
        help_text=_("Unique ticker symbol, e.g. 'AAPL'."),
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
    source_feed = models.CharField(
        verbose_name=_("Source Feed"),
        help_text=_("Indicates the data source feed."),
        max_length=100,
        blank=True,
        null=True,
    )

    # Technical Fields
    # last_sync_at = models.DateTimeField(
    #     verbose_name=_("Last Sync At"),
    #     help_text=_("The last time the ticker data was synchronized."),
    #     blank=True,
    #     null=True,
    # )

    class Meta:
        verbose_name = _("Ticker")
        verbose_name_plural = _("Tickers")
        ordering = ["ticker"]

    def __str__(self):
        return f"{self.ticker} - {self.name or _('Unnamed')}"
