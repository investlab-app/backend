from pydantic import BaseModel
from dataclasses import dataclass

class NodeData(BaseModel):
    id :str
    type :type | None
    fields :dict[str, str] = {}

class EdgeData(BaseModel):
    id_a :str
    handle_a :str
    id_b :str
    handle_b :str

class GraphData(BaseModel):
    nodes :list[NodeData] = []
    edges :list[EdgeData] = []

# class EdgeType:
#     def validate_value(self, value) -> bool:
#         pass

#     def validate_connected_output(self, edge :"EdgeType") -> bool: # Works only as input
#         pass


class Validator:

    def validate(self, data :GraphData):
        self.errors = set()

        self._check_node_types(data.nodes)
        self._check_node_id_repeats(data.nodes)
        self._validate_edges(data)

        return None, self.errors

    def _check_node_id_repeats(self, nodes :list[NodeData]):
        node_ids = set()
        for node in nodes:
            if node.id in node_ids:
                self.errors.add(IdRepeated(id=node.id))
            node_ids.add(node.id)

    def _check_node_types(self, nodes :list[NodeData]):
        for node in nodes:
            if not node.type:
                self.errors.add(InvalidNodeType(node.id))


    def _validate_edges(self, data :GraphData):
        node_ids = {n.id for n in data.nodes}

        for edge in data.edges:
            if edge.id_a not in node_ids or edge.id_b not in node_ids:
                self.errors.add(EdgeWrongID(start_id=edge.id_a, end_id=edge.id_b))

@dataclass(frozen=True)
class InvalidNodeType:
    id :str

@dataclass(frozen=True)
class IdRepeated:
    id :str

@dataclass(frozen=True)
class EdgeWrongID:
    start_id :str
    end_id :str

@dataclass(frozen=True)
class InvalidNodeField:
    id :str
    field :str

@dataclass(frozen=True)
class InvalidNodeFieldValue:
    id :str
    field :str
    value :str

@dataclass(frozen=True)
class NodeNotAllInputsConnected:
    id :str
    inputs :list[str]

@dataclass(frozen=True)
class EdgeInvalidHandle:
    from_id :str
    to_id :str
    handle :str

@dataclass(frozen=True)
class EdgeWrongDirection:
    from_id :str
    to_id :str

@dataclass(frozen=True)
class EdgeTypeMismatchOnEnds:
    from_id :str
    to_id :str

@dataclass(frozen=True)
class ConnectionDuplicate:
    from_id :str
    to_id :str

@dataclass(frozen=True)
class CycleInGraph:
    pass

@dataclass(frozen=True)
class DanglingNodeInGraph:
    pass

@dataclass(frozen=True)
class InvalidTriggerNodeCount:
    pass
