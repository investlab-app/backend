from typing import Optional
from pydantic import BaseModel

from modules.graph_lang.framework.nodes import Node, NodeFactory
import logging

logger = logging.Logger(__name__)


class NodeData(BaseModel):
    id: str
    type: str | type
    fields: dict[str, str] = {}


class EdgeData(BaseModel):
    id_a: str
    handle_a: str
    id_b: str
    handle_b: str


class GraphData(BaseModel):
    nodes: list[NodeData] = []
    edges: list[EdgeData] = []


class Parser:
    def parse(self, json: dict) -> Optional[GraphData]:
        try:
            return self._try_parse(json)
        except Exception as e:
            logger.warning(f"Failed to parse graph. Exception: %s", e)
            return None

    def _try_parse(self, json: dict) -> GraphData:
        nodes = []
        edges = []

        for node_json in json["nodes"]:
            data = {}
            for key, value in node_json["data"]["settings"].items():
                data[key] = str(value)
            if "unit" in data and "interval" in data:
                unit = data.pop("unit")
                period = data.pop("interval")
                data["timespan"] = f"{period} {unit}"
            nodes.append(
                NodeData(
                    id=node_json["id"],
                    type=node_json["type"],
                    fields=data,
                )
            )

        if "edges" in json:
            for edge_json in json["edges"]:
                edges.append(
                    EdgeData(
                        id_a=edge_json["source"],
                        handle_a=edge_json["sourceHandle"],
                        id_b=edge_json["target"],
                        handle_b=edge_json["targetHandle"],
                    )
                )

        return GraphData(nodes=nodes, edges=edges)
