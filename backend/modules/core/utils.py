import random
from decimal import ROUND_HALF_UP, Decimal

from django.utils import timezone


def get_local_datetime():
    return timezone.localtime(timezone.now())


def get_local_date():
    return get_local_datetime().date()


def get_local_time():
    return get_local_datetime().time()


def get_random_bool():
    return random.choice([True, False])


def quantize_decimal(value: Decimal, places: int = 15) -> Decimal:
    quant = Decimal("1." + "0" * places)
    return value.quantize(quant, rounding=ROUND_HALF_UP)
