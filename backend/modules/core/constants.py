from decimal import Decimal
from enum import Enum


class PrecisionType(Enum):
    price = Decimal("0.01")
    volume = Decimal("0.000000000001")

    @property
    def precision(self) -> Decimal:
        return self.value


type DecimalConvertible = Decimal | int | str
