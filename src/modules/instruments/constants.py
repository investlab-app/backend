from django.db import models
from django.utils.translation import gettext_lazy as _


class LocaleChoices(models.TextChoices):
    US = "us", _("United States")
    GLOBAL = "global", _("Global")


class MarketChoices(models.TextChoices):
    STOCKS = "stocks", _("Stocks")
    CRYPTO = "crypto", _("Crypto")
    FX = "fx", _("Foreign Exchange")
    OTC = "otc", _("Over-the-Counter")
    INDICES = "indices", _("Indices")
