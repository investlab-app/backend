from django.db import models
from django.utils.translation import gettext_lazy as _

from modules.core.models import BaseModel
from modules.core.utils import get_local_datetime
from modules.instruments.models import Instrument
from modules.investors.querysets import DepositHistoryQuerySet


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
        max_digits=30, decimal_places=2, default=0, verbose_name=_("Balance")
    )
    blocked_funds = models.DecimalField(
        max_digits=30, decimal_places=2, default=0, verbose_name=_("Blocked Funds")
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


class AccountValueSnapshot(BaseModel):
    investor = models.ForeignKey(
        Investor, on_delete=models.CASCADE, verbose_name=_("Associated Investor")
    )
    timestamp = models.DateTimeField(
        default=get_local_datetime, verbose_name=_("Datetime Of The Snapshot")
    )
    value = models.DecimalField(
        max_digits=30, decimal_places=2, verbose_name=_("Total Account Value")
    )

    class Meta:
        verbose_name = _("Account Value Snapshot")
        verbose_name_plural = _("Account Value Snapshots")
        ordering = ["-timestamp"]


class NotificationHistory(BaseModel):
    investor = models.ForeignKey(
        Investor,
        on_delete=models.CASCADE,
        related_name="notifications",
        verbose_name=_("Investor"),
    )
    type = models.CharField(max_length=50, verbose_name=_("Notification Type"))
    message_en = models.TextField(verbose_name=_("Notification Message (english)"))
    message_pl = models.TextField(verbose_name=_("Notification Message (polish)"))
    sent_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Sent At"))

    class Meta:
        verbose_name = _("Notification History")
        verbose_name_plural = _("Notification Histories")
        ordering = ["-sent_at"]

    def __str__(self):
        return f"Notification to Investor {self.investor.id} at {self.sent_at}"


class DepositHistory(BaseModel):
    investor = models.ForeignKey(
        Investor,
        on_delete=models.CASCADE,
        related_name="deposits",
        verbose_name=_("Investor"),
    )
    amount = models.DecimalField(
        max_digits=30, decimal_places=2, verbose_name=_("Deposit Amount")
    )
    deposited_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Deposited At")
    )

    objects = DepositHistoryQuerySet.as_manager()

    class Meta:
        verbose_name = _("Deposit History")
        verbose_name_plural = _("Deposit Histories")
        ordering = ["-deposited_at"]

    def __str__(self):
        return (
            f"Deposit of {self.amount} to Investor {self.investor.id} "
            f"at {self.deposited_at}"
        )
