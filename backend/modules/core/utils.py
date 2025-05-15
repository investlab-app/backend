import random

from django.utils import timezone


def get_local_datetime():
    return timezone.localtime(timezone.now())


def get_local_date():
    return get_local_datetime().date()


def get_local_time():
    return get_local_datetime().time()


def get_random_bool():
    return random.choice([True, False])
