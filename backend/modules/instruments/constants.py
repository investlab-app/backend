from django.db import models
from django.utils.translation import gettext_lazy as _


class InstrumentTypeEnum(models.TextChoices):
    CRYPTO = "CRYPTO", _("Crypto")
    COMPANY = "COMPANY", _("Company")
    ETF = "ETF", _("ETF")
    INDEX = "INDEX", _("Index")


class FiatCurrencyEnum(models.TextChoices):
    USD = "USD", _("US Dollar")
    EUR = "EUR", _("Euro")
    GBP = "GBP", _("British Pound")
