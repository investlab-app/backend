import logging

from pydantic import BaseModel

from modules.graph_lang.framework.nodes import Node

logger = logging.getLogger(__name__)


class NodeData(BaseModel):
    id: str
    type: str | type[Node]
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
    def parse(self, json: dict) -> GraphData | None:
        try:
            return self._try_parse(json)
        except Exception as e:
            logger.warning("Failed to parse graph. Exception: %s", e)
            return None

    def _try_parse(self, json: dict) -> GraphData:
        nodes = []
        edges = []

        for node_json in json["nodes"]:
            data = {}
            for key, value in node_json["data"]["settings"].items():
                data[key] = str(value)
            if "unit" in data and ("interval" in data or "period" in data):
                unit = data.pop("unit")
                if "interval" in data:
                    period = data.pop("interval")
                else:
                    period = data.pop("period")
                data["timespan"] = f"{period} {unit}"
            if "unit2" in data and "interval2" in data:
                unit2 = data.pop("unit2")
                period2 = data.pop("interval2")
                data["timespan2"] = f"{period2} {unit2}"
            nodes.append(
                NodeData(
                    id=node_json["id"],
                    type=node_json["type"],
                    fields=data,
                )
            )

        if "edges" in json:
            edges.extend(
                EdgeData(
                    id_a=edge_json["source"],
                    handle_a=edge_json["sourceHandle"],
                    id_b=edge_json["target"],
                    handle_b=edge_json["targetHandle"],
                )
                for edge_json in json["edges"]
            )

        return GraphData(nodes=nodes, edges=edges)
