from modules.prices.constants import YFinanceTimeInterval
from modules.prices.exceptions import InvalidTimeIntervalException

TRUE_STRING_VALUES = ("1", "true", "True", "TRUE", "on", "yes")


def str_to_bool(val: str | None) -> bool:
    return val in TRUE_STRING_VALUES


def str_to_list(val: str | None) -> list[str]:
    if not val:
        return []
    return list(map(str.strip, val.split(",")))


def parse_time_interval(value: str) -> YFinanceTimeInterval:
    try:
        return YFinanceTimeInterval(value)
    except ValueError as e:
        raise InvalidTimeIntervalException(
            f"Invalid time interval, valid intervals are: {", ".join([ti.value for ti in YFinanceTimeInterval])}"
        ) from e
