from django.db import models
from django.utils.translation import gettext_lazy as _

from modules.core.models import BaseModel
from modules.core.utils import get_local_datetime
from modules.instruments.models import Instrument
from modules.investors.models import Investor


class Transaction(BaseModel):
    investor = models.ForeignKey(
        Investor,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name=_("Investor"),
    )
    ticker = models.ForeignKey(
        Instrument,
        on_delete=models.CASCADE,
        related_name="transactions",
        verbose_name=_("Ticker"),
    )
    timestamp = models.DateTimeField(
        default=get_local_datetime, verbose_name=_("Timestamp")
    )
    volume = models.DecimalField(
        max_digits=30, decimal_places=15, verbose_name=_("Volume")
    )
    price = models.DecimalField(
        max_digits=20, decimal_places=2, verbose_name=_("Price")
    )
    is_buy = models.BooleanField(
        verbose_name=_("Is Buy"), help_text=_("True if buy, False if sell")
    )

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
        ordering = ["-timestamp"]

    def __str__(self):
        return f"Transaction {self.id}"
