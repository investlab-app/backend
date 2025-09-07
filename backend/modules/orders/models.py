from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

from modules.core.models import BaseModel
from modules.investors.models import Investor
from modules.instruments.models import Instrument


class Order(BaseModel):
    ticker = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)

    detail_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    detail_id = models.IntegerField()
    detail = GenericForeignKey('detail_type', 'detail_id')

    class Meta:
        indexes = [
            models.Index(fields=['detail_type', 'detail_id'])
        ]
        
class MarketOrder(models.Model):
    volume = models.IntegerField()
    volume_processed = models.IntegerField(default=0)
    is_buy = models.BooleanField()

# class LimitOrder(Order):
#     pass

# class OtherTypeOrder(Order):
#     pass