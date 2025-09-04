import base64
import random
import uuid
from collections.abc import Callable
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

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


def get_attr(obj, attr_path: str, scope_operator: str = "__"):
    """Get nested attribute from an object using a scope operator."""
    for attr in attr_path.split(scope_operator):
        obj = getattr(obj, attr, None)
        if obj is None:
            return None
    return obj


def uuid_ascii() -> str:
    """Generate a URL-safe ASCII string from a UUID."""
    u = uuid.uuid4()
    return base64.urlsafe_b64encode(u.bytes).rstrip(b"=").decode("ascii")


def get_upload_to(folder_path: str) -> Callable:
    """Generate a callable for the upload_to parameter in FileField/ImageField."""

    def upload_to(instance, filename):
        path = Path(filename)
        ext = path.suffix
        new_filename = f"{uuid_ascii()}{ext}"
        return Path(folder_path) / new_filename

    return upload_to
