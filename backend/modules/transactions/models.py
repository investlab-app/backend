from django.db import models

from modules.core.models import BaseModel
from modules.core.utils import get_local_datetime
from modules.instruments.models import Instrument
from modules.investors.models import Investor


class Transaction(BaseModel):
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    ticker = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    transaction_time = models.DateTimeField(default=get_local_datetime)
    volume = models.DecimalField(max_digits=15, decimal_places=2)
    transaction_price = models.DecimalField(max_digits=20, decimal_places=2)
    is_buy = models.BooleanField()


class TransactionHelper(BaseModel):
    buy_transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, related_name="buy"
    )
    sell_transaction = models.ForeignKey(
        Transaction, on_delete=models.CASCADE, related_name="sell"
    )
    volume = models.DecimalField(max_digits=15, decimal_places=2)
