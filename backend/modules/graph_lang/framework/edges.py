from dataclasses import dataclass, field

INPUT = 0
OUTPUT = 1


@dataclass
class EdgeType:
    direction: int
    source: str | None = None


@dataclass
class NumberType(EdgeType):
    pass


@dataclass
class EnumType(EdgeType):
    allowed_values: list[str] = field(default_factory=list)


@dataclass
class BoolType(EdgeType):
    pass


@dataclass
class TimespanType(EdgeType):
    pass


@dataclass
class VoidType(EdgeType):
    pass


@dataclass
class InstrumentType(EdgeType):
    pass
