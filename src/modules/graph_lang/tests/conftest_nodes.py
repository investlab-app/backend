from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import ExecutionContext, Node


class VoidSensorNode(Node):
    out = edges.VoidType(direction=edges.OUTPUT)
    executed = False

    def _execute(self, context):
        self.out.set(None)
        self.executed = True


class NumberBasedOnTimeNode(Node):
    out = edges.NumberType(direction=edges.OUTPUT)
    _values = {}

    def _execute(self, context: ExecutionContext):
        val = self._values[context.time_at]
        self.out.set(val)

    def set_val(self, val, time_at):
        self._values[time_at] = val


class PassNumberNode(Node):
    in_ = edges.NumberType(direction=edges.INPUT)

    out = edges.NumberType(direction=edges.OUTPUT)

    def _execute(self, context):
        self.out.set(self.in_(context))


class PriceProviderMock(Node):
    _prices = {}

    def get_price(self, ticker: str, time_at: datetime) -> Decimal:
        return self._prices[(ticker, time_at)]

    def set(self, ticker: str, time_at: datetime, price: Decimal):
        self._prices[(ticker, time_at)] = price

class SingleInputNeededNode(Node):
    in_a = edges.VoidType(direction=edges.INPUT)
    in_b = edges.VoidType(direction=edges.INPUT)

    @classmethod
    def validate_all_needed_edges(cls, edges):
        return cls.in_a in edges or cls.in_b in edges


@dataclass
class MockEdgeType(edges.EdgeType):
    validate: bool = False
    match_edge: bool = False

    def validate_value(self, value) -> bool:
        return self.validate

    def validate_connected_output(self, edge: edges.EdgeType) -> bool:
        return self.match_edge


class EmptyNode(Node):
    pass


class BoolInputNode(Node):
    text = edges.BoolType(direction=edges.INPUT)


class TwoBoolInputNode(Node):
    in_a = edges.BoolType(direction=edges.INPUT)
    in_b = edges.BoolType(direction=edges.INPUT)


class NumberOutputNode(Node):
    number = edges.NumberType(direction=edges.OUTPUT)


class NumberInputNode(Node):
    number = edges.NumberType(direction=edges.INPUT)


class NumberInputChangeSourceNode(Node):
    number = edges.NumberType(direction=edges.INPUT, source="inVal")


class NumberInputOutputNode(Node):
    in_val = edges.NumberType(direction=edges.INPUT)
    out_val = edges.NumberType(direction=edges.OUTPUT)


class TriggerNode(Node):
    TRIGGER = True


class TypeMismatchNode(Node):
    match_val = MockEdgeType(direction=edges.INPUT, validate=True, match_edge=True)
    mismatch_val = MockEdgeType(direction=edges.INPUT, validate=True, match_edge=False)


class EnumInputNode(Node):
    value = edges.EnumType(direction=edges.INPUT, allowed_values=["valid1", "valid2"])


class MockNodeFactory:
    nodes = {}

    def create_from_type(self, name: str) -> Node:
        if name not in self.nodes:
            raise ValueError
        return self.nodes[name]


class MockBoolNode(Node):
    values: dict[datetime, bool]

    out = edges.BoolType(direction=edges.OUTPUT)

    def __init__(self, inputs=None):
        super().__init__(inputs)
        self.values = {}

    def _execute(self, context: ExecutionContext):
        val = self.values[context.time_at]
        self.out.set(val)

    def set_value(self, value, date_at: datetime):
        self.values[date_at] = value


class MockNumberNode(Node):
    values: dict[datetime, Decimal]

    out = edges.BoolType(direction=edges.OUTPUT)

    def __init__(self, inputs=None):
        super().__init__(inputs)
        self.values = {}

    def _execute(self, context: ExecutionContext):
        val = self.values[context.time_at]
        self.out.set(val)

    def set_value(self, value: Decimal, date_at: datetime):
        self.values[date_at] = value
