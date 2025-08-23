import random
from decimal import ROUND_HALF_UP, Decimal

from django.utils import timezone


def get_local_datetime():
    """Get the current local date and time."""
    return timezone.localtime(timezone.now())


def get_local_date():
    """Get the current local date."""
    return get_local_datetime().date()


def get_local_time():
    """Get the current local time."""
    return get_local_datetime().time()


def get_random_bool():
    """Return a random boolean value."""
    return random.choice([True, False])


def quantize_decimal(value: Decimal, places: int = 15) -> Decimal:
    """Quantize a Decimal value to a specified number of decimal places."""
    quant = Decimal(f"1e-{places}")
    return value.quantize(quant, rounding=ROUND_HALF_UP)


def get_attr(obj, attr_path: str, scope_operator: str = '__'):
    """Get nested attribute from an object using a scope operator."""
    for attr in attr_path.split(scope_operator):
        obj = getattr(obj, attr, None)
        if obj is None:
            return None
    return obj
