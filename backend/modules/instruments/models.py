from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from modules.core.models import BaseModel
from modules.instruments.constants import FiatCurrencyEnum, InstrumentTypeEnum

class InstrumentV2(BaseModel):
    ticker = models.CharField(unique=True)
    ticker_type = models.CharField()

    delisted = models.BooleanField()

    description = models.TextField(blank=True)
    icon_url = models.URLField()
    logo_url = models.URLField()
    homepage_url = models.URLField()

    address1 = models.CharField()
    address2 = models.CharField()
    city = models.CharField()
    postal_code = models.CharField()
    state = models.CharField()

    currency_name = models.CharField()
    market = models.CharField()
    market_cap = models.DecimalField(
        max_digits=30, decimal_places=15, allow_null=True
    )
    phone_number = models.CharField()
    sector = models.CharField()
    total_employess = models.IntegerField
    

class Instrument(BaseModel):
    type = models.CharField(
        verbose_name=_("Type"), max_length=20, choices=InstrumentTypeEnum.choices
    )
    ticker = models.CharField(verbose_name=_("Ticker"), max_length=20, unique=True)
    name = models.CharField(verbose_name=_("Name"), max_length=255)
    description = models.TextField(verbose_name=_("Description"), blank=True)
    currency = models.CharField(
        verbose_name=_("Currency"), max_length=10, choices=FiatCurrencyEnum.choices
    )
    # icon = models.ImageField()

    details_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        related_name="instruments",
        verbose_name=_("Details Type"),
        null=True,
        blank=True,
        limit_choices_to=Q(
            app_label="instruments", model__in=["companydetails", "indexdetails"]
        ),
    )
    details_id = models.UUIDField(
        verbose_name=_("Details ID"), blank=True, null=True, editable=True
    )
    details = GenericForeignKey("details_type", "details_id")

    # synchronized_at = models.DateTimeField(
    #     verbose_name=_("Synchronized at"),
    #     default=get_local_datetime,
    # )

    class Meta:
        verbose_name = _("Instrument")
        verbose_name_plural = _("Instruments")

    def __str__(self):
        return f"{self.ticker} - {self.name} ({self.type})"

    def clean(self):
        """Check generic foreign key details."""
        super().clean()
        if self.details_type and not self.details_id:
            raise ValueError(_("Details ID must be set when Details Type is provided."))
        if not self.details_type and self.details_id:
            raise ValueError(_("Details Type must be set when Details ID is provided."))

    def save(self, *args, **kwargs):
        """Ensure ticker is always lowercase."""
        self.ticker = self.ticker.lower()
        super().save(*args, **kwargs)


class CompanyDetails(BaseModel):
    name = models.CharField(verbose_name=_("Company Name"), max_length=255, unique=True)
    country = models.CharField(
        verbose_name=_("Country"),
        max_length=100,
        blank=True,
        null=True,
        # TODO: add enum
    )
    industry = models.CharField(
        verbose_name=_("Industry"),
        max_length=100,
        blank=True,
        null=True,
        # TODO: add enum
    )
    website = models.URLField(verbose_name=_("Website"), blank=True, null=True)

    class Meta:
        verbose_name = _("Company Details")
        verbose_name_plural = _("Company Details")

    def __str__(self):
        return self.name


class IndexDetails(BaseModel):
    name = models.CharField(verbose_name=_("Index Name"), max_length=255, unique=True)
    fund_name = models.CharField(
        verbose_name=_("Fund Name"), max_length=255, blank=True, null=True
    )

    class Meta:
        verbose_name = _("Index Details")
        verbose_name_plural = _("Index Details")

    def __str__(self):
        return f"{self.fund_name} - {self.name}"
