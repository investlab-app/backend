from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from modules.core.models import BaseModel
from modules.instruments.models import Instrument
from modules.investors.models import Investor


class Order(BaseModel):
    ticker = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)

    detail_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    detail_id = models.IntegerField()
    detail = GenericForeignKey("detail_type", "detail_id")

    class Meta:
        indexes = [models.Index(fields=["detail_type", "detail_id"])]

    def __str__(self):
        return f"Order for {self.ticker.ticker} by investor {self.investor}"


class MarketOrder(models.Model):
    volume = models.DecimalField(max_digits=15, decimal_places=2)
    volume_processed = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_buy = models.BooleanField()

    def __str__(self):
        if self.is_buy:
            return f"Market buy order for volume: {self.volume}"
        else:
            return f"Market sell order for volume: {self.volume}"
