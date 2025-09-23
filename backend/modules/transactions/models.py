# Create your models here.
from django.db import models

from modules.core.utils import get_local_datetime
from modules.instruments.models import Instrument
from modules.investors.models import Investor


class Transaction(models.Model):
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    ticker = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    transaction_time = models.DateTimeField(default=get_local_datetime)
    volume = models.DecimalField(max_digits=30, decimal_places=15)
    transaction_price = models.DecimalField(max_digits=20, decimal_places=2)
    is_buy = models.BooleanField()

    def __str__(self):
        return f"Transaction {self.id}"
