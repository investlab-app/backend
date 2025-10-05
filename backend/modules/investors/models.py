from django.db import models
from django.utils.translation import gettext_lazy as _

from modules.core.models import BaseModel
from modules.instruments.models import Instrument


class Investor(BaseModel):
    clerk_id = models.CharField(unique=True, max_length=255, verbose_name=_("Clerk ID"))
    watching_instruments = models.ManyToManyField(
        Instrument, blank=True, verbose_name=_("Watching Instruments")
    )
    balance = models.DecimalField(
        max_digits=30, decimal_places=2, default="0", verbose_name=_("Balance")
    )

    class Meta:
        verbose_name = _("Investor")
        verbose_name_plural = _("Investors")

    def __str__(self):
        return f"Investor: {self.clerk_id}"


class Asset(BaseModel):
    investor = models.ForeignKey(
        Investor,
        on_delete=models.CASCADE,
        related_name="assets",
        verbose_name=_("Investor"),
    )
    ticker = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name="assets",
        verbose_name=_("Ticker"),
    )
    volume = models.DecimalField(
        max_digits=30, decimal_places=15, verbose_name=_("Volume")
    )

    class Meta:
        verbose_name = _("Asset")
        verbose_name_plural = _("Assets")
        unique_together = ("investor", "ticker")

    def __str__(self):
        return f"{self.ticker} Asset. Volume: {self.volume}"


class AccountValueSnapshot(BaseModel):
    investor = models.ForeignKey(
        Investor, on_delete=models.CASCADE, verbose_name=_("Associated Investor")
    )
    timestamp = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Datetime Of The Snapshot")
    )
    value = models.DecimalField(
        max_digits=30, decimal_places=2, verbose_name=_("Total Account Value")
    )

    class Meta:
        verbose_name = _("Account Value Snapshot")
        verbose_name_plural = _("Account Value Snapshots")
        ordering = ["-timestamp"]
