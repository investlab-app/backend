TRUE_STRING_VALUES = ("1", "true", "True", "TRUE", "on", "yes")


def str_to_bool(val: str | None) -> bool:
    return val in TRUE_STRING_VALUES


def str_to_list(val: str | None) -> list[str]:
    if not val:
        return []
    return list(map(str.strip, val.split(",")))
