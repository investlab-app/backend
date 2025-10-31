from pydantic import BaseModel

from modules.graph_lang.framework.nodes import Node


class NodeData(BaseModel):
    id: str
    type: type[Node] | None
    fields: dict[str, str] = {}


class EdgeData(BaseModel):
    id_a: str
    handle_a: str
    id_b: str
    handle_b: str


class GraphData(BaseModel):
    nodes: list[NodeData] = []
    edges: list[EdgeData] = []
