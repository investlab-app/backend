from django.db import models

from modules.core.models import BaseModel
from modules.core.utils import get_local_datetime
from modules.investors.models import Investor


class Transaction(BaseModel):
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    ticker = models.CharField()  # Relation
    transaction_time = models.DateTimeField(default=get_local_datetime)
    volume = models.IntegerField()  # Decimal
    transaction_price = models.DecimalField(max_digits=20, decimal_places=2)
    is_buy = models.BooleanField()


class TransactionHelper(BaseModel):
    buy_transaction = models.ForeignKey(  # buy_transaction
        Transaction, on_delete=models.CASCADE, related_name="buy"
    )
    sell_transaction = models.ForeignKey(  # sell_transaction
        Transaction, on_delete=models.CASCADE, related_name="sell"
    )
    volume = models.IntegerField()
