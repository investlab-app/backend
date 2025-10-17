from django.db import models
from django.utils.translation import gettext_lazy as _

from modules.core.models import BaseModel
from modules.instruments.models import Instrument


class Investor(BaseModel):
    clerk_id = models.CharField(unique=True, max_length=255, verbose_name=_("Clerk ID"))
    language = models.CharField(
        max_length=10,
        default="en",
        verbose_name=_("Language"),
        help_text=_("User's preferred language (e.g., 'en', 'pl')"),
    )

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
        return f"Investor {self.id} (Clerk ID: {self.clerk_id})"


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
