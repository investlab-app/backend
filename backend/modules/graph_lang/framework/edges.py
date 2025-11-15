from dataclasses import dataclass, field
from datetime import timedelta
from decimal import Decimal
from typing import Any

from modules.instruments.models import Instrument

INPUT = 0
OUTPUT = 1


@dataclass
class EdgeType:
    direction: int
    source: str | None = None
    field_name: str | None = None

    @property
    def source_name(self) -> str:
        if self.source is not None:
            return self.source
        else:
            return self.field_name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return instance.__dict__[self.field_name]

    def __set__(self, instance, value):
        instance.__dict__[self.field_name] = value

    def __set_name__(self, owner, name):
        self.field_name = name

    def parse(self, value) -> Any:
        raise NotImplementedError

    def validate_connected_output(self, other: "EdgeType") -> bool:
        return isinstance(other, type(self))

    def validate_value(self, value) -> bool:
        raise NotImplementedError


@dataclass
class NumberType(EdgeType):
    def validate_value(self, value) -> bool:
        try:
            Decimal(value)
            return True
        except ValueError:
            return False

    def parse(self, value) -> Decimal:
        return Decimal(value)


@dataclass
class EnumType(EdgeType):
    allowed_values: list[str] = field(default_factory=list)

    def validate_connected_output(self, other):
        raise NotImplementedError

    def validate_value(self, value) -> bool:
        return value in self.allowed_values

    def parse(self, value) -> str:
        if not self.validate_value(value):
            raise ValueError
        return value


@dataclass
class BoolType(EdgeType):
    def validate_value(self, value: Any) -> bool:
        if isinstance(value, bool):
            return True

        return value.lower() in ("true", "false")

    def parse(self, value) -> bool:
        return bool(value)


@dataclass
class TimespanType(EdgeType):
    def validate_value(self, value: Any):
        if isinstance(value, timedelta):
            return True

        try:
            interval, unit = value.split(" ")
            assert unit in ["day", "hour", "week", "month"]
            int(interval)
            return True
        except Exception:
            return False

    def parse(self, value: str) -> timedelta:
        if isinstance(value, timedelta):
            return value

        interval, unit = value.split(" ")
        interval = int(interval)
        if unit == "day":
            return timedelta(days=interval)
        if unit == "month":
            return timedelta(days=30 * interval)
        if unit == "week":
            return timedelta(weeks=interval)
        if unit == "hour":
            return timedelta(hours=interval)


@dataclass
class VoidType(EdgeType):
    def validate_value(self, value):
        return True

    def parse(self, value):
        return None


@dataclass
class InstrumentType(EdgeType):
    def validate_value(self, value: str):
        return Instrument.objects.filter(ticker__iexact=value).exists()

    def parse(self, value):
        return value
