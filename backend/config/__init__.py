import logging

from modules.prices.constants import YFinanceTimeInterval
from modules.prices.exceptions import InvalidTimeIntervalException

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s"
)


TRUE_STRING_VALUES = ("1", "true", "True", "TRUE", "on", "yes")


def str_to_bool(val: str | None) -> bool:
    return val in TRUE_STRING_VALUES


def str_to_list(val: str | None) -> list[str]:
    """
    Converts a comma-separated string into a list of trimmed strings.
    
    Returns an empty list if the input is None or an empty string.
    """
    if not val:
        return []
    return list(map(str.strip, val.split(",")))


def parse_time_interval(value: str) -> YFinanceTimeInterval:
    """
    Converts a string to a YFinanceTimeInterval enum member.
    
    Raises:
        InvalidTimeIntervalException: If the input string does not match any valid interval. The exception message lists all valid interval values.
    
    Returns:
        The corresponding YFinanceTimeInterval enum member.
    """
    try:
        return YFinanceTimeInterval(value)
    except ValueError as e:
        valid_intervals = ", ".join([ti.value for ti in YFinanceTimeInterval])
        raise InvalidTimeIntervalException(
            f"Invalid time interval, valid intervals are: {valid_intervals}"
        ) from e
