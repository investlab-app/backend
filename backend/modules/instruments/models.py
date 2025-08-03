from django.db import models
from modules.core.models import BaseModel

class Instrument(BaseModel):
    ticker = models.CharField(unique=True)
    ticker_type = models.CharField()
    delisted = models.BooleanField()

    description = models.TextField(blank=True, default="No description")
    icon_url = models.URLField(null=True)
    logo_url = models.URLField(null=True)
    homepage_url = models.URLField(null=True)
    currency_name = models.CharField(null=True)
    market = models.CharField(null=True)
    market_cap = models.DecimalField(max_digits=30, decimal_places=15, null=True)
    phone_number = models.CharField(null=True)
    sector = models.CharField(null=True)
    total_employess = models.IntegerField(null=True)