from datetime import datetime
from typing import Any

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

class NodeMeta(type):
    def __init__(cls, name, bases, dct):
        cls._assign_names_to_edges()

    def _assign_names_to_edges(cls):
        edge_names = [
            name 
            for name in dir(cls)
            if isinstance(getattr(cls, name), edges.EdgeType)
        ]

        for name in edge_names:
            edge = getattr(cls, name)
            edge.field_name = name


class Node(metaclass=NodeMeta):
    _time_at: datetime | None = None
    all_edges: list
    id: str | None
    TRIGGER = False

    def __init__(self):
        edge_names = self._get_edge_attrs()
        self._copy_edges_to_list(edge_names)
        self._replace_edge_fields(edge_names)

    def _get_edge_attrs(self) -> list[str]:
        return [
            name
            for name in dir(self)
            if isinstance(getattr(self, name), edges.EdgeType)
        ]

    def _copy_edges_to_list(self, edge_names):
        self.all_edges = []
        for name in edge_names:
            edge = getattr(self, name)
            edge.field_name = name
            self.all_edges.append(edge)

    def _replace_edge_fields(self, edge_names):
        for f in edge_names:
            edge: edges.EdgeType = getattr(self, f)
            if edge.direction == edges.INPUT:
                setattr(self, f, NodeInput(self))
            else:
                setattr(self, f, NodeOutput(self))

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
        return next((
            e 
            for e in cls.get_all_edges() 
            if e.source_name == source_name)
        , None)

    def execute(self):
        pass

    def set_execution_time(self, time_at: datetime):
        self._time_at = time_at

    def get_execution_time(self) -> datetime:
        return self._time_at


class NodeFactory:
    def from_type(self, type: type[Node]) -> Node:
        pass

    def name_to_type(self, name: str) -> type[Node]:
        pass
