from datetime import datetime, timedelta
from typing import Any, Optional
from dataclasses import dataclass
from modules.graph_lang.framework.price_provider import PrefetchRange

from modules.graph_lang.framework.actions import GraphActionSet
from modules.graph_lang.framework.price_provider import PriceProvider
from modules.graph_lang.framework import edges


@dataclass
class ExecutionContext:
    price_provider: Any
    effects: set
    time_at: datetime


class NodeOutput:
    node: "Node"
    name: str
    value: Any

    def __init__(self, node):
        self.node = node

    def get(self, context):
        self.node.execute(context)
        return self.value

    def set(self, value):
        self.value = value


class NodeInput:
    node: "Node"

    output: NodeOutput | None = None
    validated_value: Any | None = None
    raw_value: Any | None = None

    def __init__(self, node: "Node", og_edge: edges.EdgeType):
        self.node = node
        self.edge = og_edge

    def __call__(self, context: ExecutionContext):
        if self.output is not None:
            return self.output.get(context)
        else:
            return self.edge.parse(self.validated_value)

    def set(self, value):
        self.validated_value = value

    def connect(self, output: NodeOutput):
        self.output = output

    def get_raw_value(self):
        return self.raw_value

    def set_raw_value(self, value):
        self.raw_value = value


class NodeUtilsMixin:
    def get_first_output(self) -> NodeOutput:
        edge_list = type(self).get_all_edges()
        for e in edge_list:
            if e.direction == edges.OUTPUT:
                return getattr(self, e.field_name)

    def get_io_by_source_name(self, source_name) -> NodeInput | NodeOutput:
        edge = type(self).get_edge_by_source_name(source_name)
        return getattr(self, edge.field_name)

    @classmethod
    def get_incoming_edges(cls) -> list[edges.EdgeType]:
        return [
            getattr(cls, name)
            for name in dir(cls)
            if isinstance(getattr(cls, name), edges.EdgeType)
            and getattr(cls, name).direction == edges.INPUT
        ]

    @classmethod
    def get_all_edges(cls) -> list[edges.EdgeType]:
        return [
            getattr(cls, name)
            for name in dir(cls)
            if isinstance(getattr(cls, name), edges.EdgeType)
        ]

    @classmethod
    def get_edge_by_source_name(cls, source_name) -> edges.EdgeType | None:
        return next(
            (e for e in cls.get_all_edges() if e.source_name == source_name), None
        )


class Node(NodeUtilsMixin):
    all_edges: list
    id: str | None
    TRIGGER = False
    TYPE_NAME = None

    def __init__(self, inputs={}):
        self._initialize_input_outputs()
        self._pass_data_to_inputs(inputs)

    def _initialize_input_outputs(self):
        for name, field in self.__class__.__dict__.items():
            if isinstance(field, edges.EdgeType):
                if field.direction == edges.INPUT:
                    value = NodeInput(self, field)
                else:
                    value = NodeOutput(self)
                setattr(self, name, value)

    def _pass_data_to_inputs(self, inputs):
        edges = type(self).get_incoming_edges()
        for name, value in inputs.items():
            edge = next((e for e in edges if e.source_name == name), None)
            if not edge:
                continue

            field: NodeInput = getattr(self, edge.field_name)
            if self._is_output_name_and_node_pair(value):
                output_name = value[0]
                node: Node = value[1]
                output = node.get_io_by_source_name(output_name)

                field.connect(output)
            elif isinstance(value, Node):
                field.connect(value.get_first_output())
            else:
                field.set(value)

    def _is_output_name_and_node_pair(self, value):
        return (
            isinstance(value, tuple)
            and len(value) == 2
            and isinstance(value[0], str)
            and isinstance(value[1], Node)
        )

    def execute(self, context: "ExecutionContext"):
        pass

    def calculate_needed_historical_prices(self):
        children_ranges: dict[str, PrefetchRange] = {}
        edges = self.get_incoming_edges()
        for e in edges:
            edge = getattr(self, e.field_name)

            if edge.output:
                child_range = edge.output.node.calculate_needed_historical_prices()
                children_ranges = self._combine_price_ranges(
                    children_ranges, child_range
                )

        self_prices = self._get_needed_prices()
        children_ranges = self._combine_price_ranges(children_ranges, self_prices)
        for key in children_ranges:
            children_ranges[key] = children_ranges[key] + self._get_working_timespan()
        return children_ranges

    def _combine_price_ranges(
        self,
        d1: dict[str, timedelta],
        d2: dict[str, timedelta],
    ):
        result = {}
        common_tickers = set(d1.keys()).intersection(set(d2.keys()))

        for ticker in common_tickers:
            result[ticker] = max(d1[ticker], d2[ticker])

        for ticker in d1:
            if not ticker in common_tickers:
                result[ticker] = d1[ticker]

        for ticker in d2:
            if not ticker in common_tickers:
                result[ticker] = d2[ticker]

        return result

    # Can be overridden
    def _get_working_timespan(self) -> timedelta:
        return timedelta()

    # Can be overridden
    def _get_needed_prices(self) -> dict[str, timedelta]:
        return {}


class NodeFactory:
    def __init__(self):
        self._types = {
            cls.TYPE_NAME.lower(): cls
            for cls in Node.__subclasses__()
            if cls.TYPE_NAME is not None
        }

    def name_to_type(self, name):
        return self._types.get(name.lower())

    def from_type(self, node_type):
        if not issubclass(node_type, Node):
            raise ValueError(f"{node_type} is not a subclass of Node")
        return node_type()

    def type_exists(self, name):
        return name.lower() in self._types
