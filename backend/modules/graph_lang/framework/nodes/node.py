from dataclasses import dataclass
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
    value: Any | None

    def __init__(self, node: "Node"):
        self.node = node

    def __call__(self, execution_time = None):
        if self.output is not None:
            self._propagate_execution_time(execution_time)
            return self.output.get()
        else:
            return self.value

    def _propagate_execution_time(self, execution_time):
        if execution_time is None:
            execution_time = self.node._time_at
        self.output.node.set_execution_time(execution_time)

    def set(self, value):
        self.value = value

    def connect(self, output: NodeOutput):
        self.output = output


class Node:
    _time_at: datetime = None

    def __init__(self):
        edge_names = self._get_edge_attrs()
        self._replace_edge_fields(edge_names)

    def _get_edge_attrs(self) -> list[str]:
        return [
            name
            for name in dir(self)
            if isinstance(getattr(self, name), edges.EdgeType)
        ]

    def _replace_edge_fields(self, edge_names):
        for f in edge_names:
            edge: edges.EdgeType = getattr(self, f)
            if edge.direction == edges.INPUT:
                setattr(self, f, NodeInput(self))
            else:
                setattr(self, f, NodeOutput(self))

    def execute(self):
        pass

    def set_execution_time(self, time_at :datetime):
        self._time_at = time_at


class NodeData:
    value: Any

    def __call__(self, time_at=None):
        return self.value
