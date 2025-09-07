from django.db import models

from modules.core.models import BaseModel


class LatestPrice(BaseModel):
    ticker = models.CharField()
    price = models.DecimalField(max_digits=30, decimal_places=2)
