from datetime import datetime
from typing import Any, Optional
from dataclasses import dataclass
from modules.graph_lang.framework.price_provider import PrefetchRange

from modules.graph_lang.framework.actions import GraphActionSet
from modules.graph_lang.framework.price_provider import PriceProvider
from modules.graph_lang.framework import edges

class NodeOutput:
    node: "Node"
    name: str
    value: Any

    def __init__(self, node):
        self.node = node

    def get(self):
        self.node.execute()
        return self.value

    def set(self, value):
        self.value = value


class NodeInput:
    node: "Node"

    output: NodeOutput | None = None
    validated_value: Any | None = None
    raw_value: Any | None = None

    def __init__(self, node: "Node"):
        self.node = node

    def __call__(self, execution_time=None):
        if self.output is not None:
            self._propagate_execution_time(execution_time)
            return self.output.get()
        else:
            return self.validated_value

    def _propagate_execution_time(self, execution_time):
        if execution_time is None:
            execution_time = self.node.get_execution_time()
        self.output.node.set_execution_time(execution_time)

    def set(self, value):
        self.validated_value = value

    def connect(self, output: NodeOutput):
        self.output = output

    def get_raw_value(self):
        return self.raw_value

    def set_raw_value(self, value):
        self.raw_value = value


class Node:
    _time_at: datetime | None = None
    all_edges: list
    id: str | None
    TRIGGER = False
    TYPE_NAME = None

    def __init__(self):
        self.initialize_input_outputs()

    def initialize_input_outputs(self):
        for name, field in self.__class__.__dict__.items():
            if isinstance(field, edges.EdgeType):
                if field.direction == edges.INPUT:
                    value = NodeInput(self)
                else:
                    value = NodeOutput(self)
                setattr(self, name, value)

    def get_input_by_source_name(self, source_name) -> NodeInput:
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

    def execute(self):
        pass

    def set_execution_time(self, time_at: datetime):
        self._time_at = time_at

    def get_execution_time(self) -> datetime:
        return self._time_at

    def prefetch_data(self, data_range :PrefetchRange):
        new_data_range = self._get_new_time_range(data_range)
        self._prefetch_data(new_data_range)

        edges = self.get_incoming_edges()
        for e in edges:
            edge = getattr(self, e.field_name)
            edge.output.node.prefetch_data(new_data_range)
    
    # Can be overridden
    def _get_new_time_range(self, data_range :PrefetchRange) -> PrefetchRange:
        return data_range

    # Can be overridden
    def _prefetch_data(self, data_range :PrefetchRange):
        pass





class NodeFactory:
    def __init__(self, price_provider, action_set):
        self._price_provider = price_provider
        self._action_set = action_set
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
        return node_type(
            price_provider=self._price_provider, action_set=self._action_set
        )

    def type_exists(self, name):
        return name.lower() in self._types
