from decimal import Decimal
from enum import Enum

from rest_framework import serializers


class DecimalField(serializers.DecimalField):
    def __init__(self, max_digits=30, decimal_places=15, *args, **kwargs):
        super().__init__(max_digits, decimal_places, *args, **kwargs)


class PrecisionType(Enum):
    price = Decimal("0.01")
    volume = Decimal("0.000000000001")

    @property
    def precision(self) -> Decimal:
        return self.value
