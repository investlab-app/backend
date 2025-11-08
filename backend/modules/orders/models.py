from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _

from modules.core.models import BaseModel
from modules.instruments.models import Instrument
from modules.investors.models import Investor


class Order(BaseModel):
    ticker = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name=_("Ticker"),
    )
    investor = models.ForeignKey(
        Investor,
        on_delete=models.CASCADE,
        related_name="orders",
        verbose_name=_("Investor"),
    )

    detail_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="orders",
        limit_choices_to=(
            models.Q(app_label="orders")
            & models.Q(model__in=["marketorder", "limitorder"])
        ),
    )
    detail_id = models.UUIDField()
    detail = GenericForeignKey("detail_type", "detail_id")

    class Meta:
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")
        indexes = [models.Index(fields=["detail_type", "detail_id"])]


class MarketOrder(BaseModel):
    volume = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name=_("Volume")
    )
    volume_processed = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name=_("Volume Processed")
    )
    is_buy = models.BooleanField(verbose_name=_("Is Buy"))
    blocked_funds = models.DecimalField(
        max_digits=30, decimal_places=2, default="0", verbose_name=_("Blocked Funds")
    )

    class Meta:
        verbose_name = _("Market Order")
        verbose_name_plural = _("Market Orders")

    def __str__(self):
        return f"Market order for volume: {self.volume}. Buy: {self.is_buy}"


class LimitOrder(BaseModel):
    volume = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name=_("Volume")
    )
    volume_processed = models.DecimalField(
        max_digits=15, decimal_places=2, default=0, verbose_name=_("Volume Processed")
    )
    is_buy = models.BooleanField(verbose_name=_("Is Buy"))
    limit_price = models.DecimalField(
        max_digits=30, decimal_places=8, verbose_name=_("Limit Price")
    )
    blocked_funds = models.DecimalField(
        max_digits=30, decimal_places=2, default="0", verbose_name=_("Blocked Funds")
    )

    class Meta:
        verbose_name = _("Limit Order")
        verbose_name_plural = _("Limit Orders")

    def __str__(self):
        return f"Limit order for volume: {self.volume}. Buy: {self.is_buy} @ {self.limit_price}"
