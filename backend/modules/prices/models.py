from django.db import models
from django.utils.translation import gettext_lazy as _

from modules.core.models import BaseModel
from modules.instruments.models import Instrument
from modules.notifications.models import NotificationConfig

class PriceAlert(BaseModel):
    instrument = models.ForeignKey(
        Instrument, on_delete=models.CASCADE, verbose_name=_("Instrument")
    )
    notification_config = models.ForeignKey(
        NotificationConfig, on_delete=models.CASCADE
    )
    threshold_type = models.CharField(
        max_length=10,
        choices=[
            ("above", _("Above")),
            ("below", _("Below")),
        ],
        verbose_name=_("Threshold Type"),
    )
    threshold_value = models.DecimalField(
        max_digits=10, decimal_places=2, verbose_name=_("Threshold Value")
    )

    class Meta:
        unique_together = (
            "investor",
            "instrument",
            "threshold_type",
            "threshold_value",
        )
        verbose_name = _("Price Alert")
        verbose_name_plural = _("Price Alerts")

    def __str__(self):
        return (
            f"Price Alert: {self.investor} - {self.instrument.symbol} "
            f"({self.threshold_type} {self.threshold_value})"
        )