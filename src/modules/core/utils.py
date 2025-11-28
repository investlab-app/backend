import base64
import random
import uuid
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from zoneinfo import ZoneInfo

from django.utils import timezone
from django.utils.deconstruct import deconstructible


def get_local_datetime():
    """Get the current local date and time."""
    return timezone.localtime(timezone.now())


def get_local_date():
    """Get the current local date."""
    return get_local_datetime().date()


def get_local_time():
    """Get the current local time."""
    return get_local_datetime().time()


def get_new_york_datetime():
    """Get the current date and time in New York timezone."""
    ny_tz = ZoneInfo("America/New_York")
    return timezone.now().astimezone(ny_tz)


def get_random_bool():
    """Return a random boolean value."""
    return random.choice([True, False])


def quantize_decimal(value: Decimal, places: int = 15) -> Decimal:
    """Quantize a Decimal value to a specified number of decimal places."""
    quant = Decimal(f"1e-{places}")
    return value.quantize(quant, rounding=ROUND_HALF_UP)


def to_quantized_decimal(value: Decimal | float | str, places: int = 15) -> Decimal:
    """Convert a value to Decimal and quantize it."""
    return quantize_decimal(Decimal(value), places)


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


def upload_to(
    instance, filename, *, folder_path: str = "_uploads/", uuid_as_name: bool = True
):
    """
    Function for upload_to FileField/ImageField model parameter.
    To pass folder_path and uuid_as_name please use with functools.partial.

    Usage:
        image = models.ImageField(upload_to=partial(upload_to, folder_path='images/'))

    """
    name = uuid_ascii() if uuid_as_name else Path(filename).stem
    ext = Path(filename).suffix
    return Path(folder_path) / f"{name}{ext}"


@deconstructible
class UploadTo:
    """
    Callable class for upload_to FileField/ImageField model parameter.

    Usage:
        image = models.ImageField(upload_to=UploadTo('images/'))
    """

    def __init__(self, folder_path: str, *, uuid_as_name: bool = True):
        self.folder_path = folder_path
        self.uuid_as_name = uuid_as_name

    def __call__(self, instance, filename):
        return str(self.generate_path(filename))

    def generate_path(self, filename: str) -> Path:
        name = uuid_ascii() if self.uuid_as_name else Path(filename).stem
        ext = Path(filename).suffix
        return Path(self.folder_path) / f"{name}{ext}"
