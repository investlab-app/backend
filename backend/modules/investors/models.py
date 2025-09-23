from django.db import models
from django.utils.translation import gettext_lazy as _

from modules.instruments.models import Instrument


class Investor(models.Model):
    clerk_id = models.CharField(unique=True, max_length=255, verbose_name=_("Clerk ID"))
    watching_instruments = models.ManyToManyField(Instrument, blank=True)
    balance = models.DecimalField(max_digits=30, decimal_places=2, default="0")

    def __str__(self):
        return f"Investor: {self.clerk_id}"


class Asset(models.Model):
    pk = models.CompositePrimaryKey("investor", "ticker")
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    ticker = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    volume = models.DecimalField(max_digits=30, decimal_places=15)