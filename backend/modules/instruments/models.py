from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils.translation import gettext_lazy as _
from django.db import models

from modules.core.models import BaseModel
from modules.instruments.constants import InstrumentTypeEnum, FiatCurrencyEnum


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

    # detail_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    # detail_object_id = models.UUIDField()
    # detail = GenericForeignKey('detail_content_type', 'detail_object_id')

    class Meta:
        verbose_name = _("Instrument")
        verbose_name_plural = _("Instruments")

    def __str__(self):
        return f"{self.ticker} - {self.name} ({self.type})"

    def save(self, *args, **kwargs):
        """Ensure ticker is always lowercase."""
        self.ticker = self.ticker.lower()
        super().save(*args, **kwargs)
