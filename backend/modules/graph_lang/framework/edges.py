from dataclasses import dataclass, field
from typing import Any

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

    def parse(self, value) -> Any:
        raise NotImplementedError

    def validate_connected_output(self, other: "EdgeType") -> bool:
        raise NotImplementedError

    def validate_value(self, value) -> bool:
        raise NotImplementedError


@dataclass
class NumberType(EdgeType):
    def validate_connected_output(self, other: EdgeType) -> bool:
        return isinstance(other, NumberType)

    def validate_value(self, value) -> bool:
        try:
            int(value)
            return True
        except ValueError:
            return False

    def parse(self, value) -> int:
        return int(value)


@dataclass
class EnumType(EdgeType):
    allowed_values: list[str] = field(default_factory=list)

    def validate_value(self, value) -> bool:
        return value in self.allowed_values

    def parse(self, value) -> str:
        if not self.validate_value(value):
            raise ValueError
        return value


@dataclass
class BoolType(EdgeType):
    def validate_value(self, value) -> bool:
        return value.lower() in ("true", "false")

    def parse(self, value) -> bool:
        return bool(value)


@dataclass
class TimespanType(EdgeType):
    pass


@dataclass
class VoidType(EdgeType):
    pass


@dataclass
class InstrumentType(EdgeType):
    pass
