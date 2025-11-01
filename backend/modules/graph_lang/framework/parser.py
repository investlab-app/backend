from typing import Optional
from pydantic import BaseModel

from modules.graph_lang.framework.nodes import Node, NodeFactory


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

# TODO implement
# TODO implement node factory
class Parser:
    def __init__(self, node_factory :NodeFactory = None):
        self._node_factory = node_factory or NodeFactory()

    def parse(self, json :dict) -> Optional[GraphData]:
        try:
            return self._try_parse(json)
        except Exception:
            return None

    def try_parse(self, json :dict) -> GraphData:
        nodes = []
        edges = []

        for node_json in json['nodes']:
            data = {}
            for key, value in node_json['settings']['data']:
                data[key] = value
            nodes.append(NodeData(
                id = node_json['id'],
                type=self._node_factory.name_to_type(node_json['type']),
                fields=data
            ))

        for edge_json in json['edges']:
            edges.append(EdgeData(
                id_a=edge_json['source'],
                handle_a=edge_json['sourceHandle'],
                id_b=edge_json['target'],
                handle_b=edge_json['targetHandle']
            ))

        return GraphData(
            nodes=nodes,
            edges=edges
        )
