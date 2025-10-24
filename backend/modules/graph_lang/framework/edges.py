from dataclasses import dataclass

INPUT = 0
OUTPUT = 1

@dataclass
class EdgeType:
    direction :int
    source :str | None

@dataclass
class NumberType(EdgeType):
    pass

@dataclass
class EnumType(EdgeType):
    allowed_values :list[str]

@dataclass
class BoolType(EdgeType):
    pass

@dataclass
class TimespanType(EdgeType):
    pass

@dataclass
class InstrumentType(EdgeType):
    pass