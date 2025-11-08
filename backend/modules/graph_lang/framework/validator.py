from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field

from modules.graph_lang.framework import edges
from modules.graph_lang.framework.parser import EdgeData, GraphData, NodeData
from modules.graph_lang.framework.nodes import NodeFactory


class Validator:

    def __init__(self, node_factory :NodeFactory = None):
        self._node_factory = node_factory or NodeFactory()

    # TODO: catch any unknown error, return unknown validation error
    # TODO: try to build the graph at the end
    # TODO: implement trigger node at the top check
    def validate(self, data: GraphData):
        data = deepcopy(data)
        self.errors = []

        self._assign_node_types(data.nodes)
        self._check_node_types(data.nodes)
        self._check_node_id_repeats(data.nodes)
        self._validate_edges_ids(data)

        if self.errors:
            return self.errors

        self._validate_node_field_types(data.nodes)
        self._validate_node_field_values(data.nodes)
        self._validate_node_all_inputs_connected(data)
        self._validate_edge_handle_names(data)
        self._validate_edge_direction(data)
        self._validate_edge_type_mismatch(data)
        self._validate_edge_duplicates(data.edges)

        if self.errors:
            return self.errors

        self._validate_cycles(data)
        self._validate_dangling_nodes(data)
        self._validate_triggers(data.nodes)
        return self.errors

    def _assign_node_types(self, nodes: list[NodeData]):
        for n in nodes:
            if self._node_factory.type_exists(n.type):
                n.type = self._node_factory.name_to_type(n.type)
            else:
                n.type = ''

    def _check_node_id_repeats(self, nodes: list[NodeData]):
        node_ids = set()
        for node in nodes:
            if node.id in node_ids:
                self.errors.append(IdRepeated(id=node.id))
            node_ids.add(node.id)

    def _check_node_types(self, nodes: list[NodeData]):
        for node in nodes:
            if not node.type:
                self.errors.append(InvalidNodeType(id=node.id))

    def _validate_edges_ids(self, data: GraphData):
        node_ids = {n.id for n in data.nodes}

        for edge in data.edges:
            if edge.id_a not in node_ids or edge.id_b not in node_ids:
                self.errors.append(EdgeWrongID(start_id=edge.id_a, end_id=edge.id_b))

    def _validate_node_field_types(self, nodes: list[NodeData]):
        for node in nodes:
            edges = node.type.get_incoming_edges()

            for field in node.fields:
                if not any(field == e.source_name for e in edges):
                    self.errors.append(InvalidNodeField(id=node.id, field=field))

    def _validate_node_field_values(self, nodes: list[NodeData]):
        for node in nodes:
            edges = node.type.get_incoming_edges()

            for field, value in node.fields.items():
                edge = next((e for e in edges if field == e.source_name), None)
                if not edge:
                    return
                if not edge.validate_value(value):
                    self.errors.append(
                        InvalidNodeFieldValue(id=node.id, field=field, value=value)
                    )

    def _validate_node_all_inputs_connected(self, graph: GraphData):
        nodes = graph.nodes
        edges = graph.edges

        for node in nodes:
            names = {e.source_name for e in node.type.get_incoming_edges()}

            for field in node.fields:
                if field in names:
                    names.remove(field)

            for edge in edges:
                if edge.id_a == node.id and edge.handle_a in names:
                    names.remove(edge.handle_a)
                if edge.id_b == node.id and edge.handle_b in names:
                    names.remove(edge.handle_b)

            if names:
                self.errors.append(NodeNotAllInputsConnected(node.id, list(names)))

    def _validate_edge_handle_names(self, graph: GraphData):
        edges = graph.edges
        nodes = {n.id: n for n in graph.nodes}

        for edge in edges:
            if edge.id_a in nodes:
                self._validate_edge_handle(edge, nodes[edge.id_a], edge.handle_a)

            if edge.id_b in nodes:
                self._validate_edge_handle(edge, nodes[edge.id_b], edge.handle_b)

    def _validate_edge_handle(self, edge: EdgeData, node: NodeData, handle: str):
        names = {e.source_name for e in node.type.get_all_edges()}
        if handle not in names:
            self.errors.append(EdgeInvalidHandle(edge.id_a, edge.id_b, handle))

    def _validate_edge_direction(self, graph: GraphData):
        edges = graph.edges
        nodes = {n.id: n for n in graph.nodes}

        for edge in edges:
            id_a, id_b = edge.id_a, edge.id_b
            if id_a not in nodes or id_b not in nodes:
                continue

            edge_a = nodes[id_a].type.get_edge_by_source_name(edge.handle_a)
            edge_b = nodes[id_b].type.get_edge_by_source_name(edge.handle_b)

            if not edge_a or not edge_b:
                continue

            if edge_a.direction == edge_b.direction:
                self.errors.append(EdgeWrongDirection(id_a, id_b))

    def _validate_edge_type_mismatch(self, graph):
        nodes: dict[str, NodeData] = {n.id: n for n in graph.nodes}

        for edge in graph.edges:
            id_a, id_b = edge.id_a, edge.id_b
            if id_a not in nodes or id_b not in nodes:
                continue

            edge_a = nodes[id_a].type.get_edge_by_source_name(edge.handle_a)
            edge_b = nodes[id_b].type.get_edge_by_source_name(edge.handle_b)
            if not edge_a or not edge_b:
                continue

            if edge_a.direction == edge_b.direction:
                continue

            receiving_edge = edge_a if edge_a.direction == edges.INPUT else edge_b
            sending_edge = edge_b if edge_a.direction == edges.INPUT else edge_a

            if not receiving_edge.validate_connected_output(sending_edge):
                self.errors.append(EdgeTypeMismatchOnEnds(id_a, id_b))

    def _validate_edge_duplicates(self, edges: list[EdgeData]):
        conn_counter = defaultdict(int)

        for e in edges:
            conn_counter[(e.id_a, e.id_b)] += 1
            conn_counter[(e.id_b, e.id_a)] += 1

        errors = set()
        for e in edges:
            if conn_counter[(e.id_a, e.id_b)] > 1 or conn_counter[(e.id_b, e.id_a)] > 1:
                errors.add((e.id_a, e.id_b))

        for id_a, id_b in errors:
            self.errors.append(ConnectionDuplicate(id_a, id_b))

    def _validate_cycles(self, graph: GraphData):
        nodes = {n.id: n for n in graph.nodes}
        # Build adjacency list
        adj = defaultdict(list)
        for e in graph.edges:
            edge = nodes[e.id_a].type.get_edge_by_source_name(e.handle_a)
            if edge.direction == edges.INPUT:
                adj[e.id_a].append(e.id_b)
            else:
                adj[e.id_b].append(e.id_a)

        # Find top level node (no incoming edges)
        all_nodes = set(nodes.keys())
        incoming = set()
        for targets in adj.values():
            incoming.update(targets)
        top_level_nodes = list(all_nodes - incoming)
        if not top_level_nodes:
            self.errors.append(CycleInGraph())
            return
        top_level_node = top_level_nodes[0]

        visited = set()
        rec_stack = set()

        def dfs(node_id):
            visited.add(node_id)
            rec_stack.add(node_id)
            for neighbor in adj[node_id]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node_id)
            return False

        if dfs(top_level_node):
            self.errors.append(CycleInGraph())

    def _validate_dangling_nodes(self, graph: GraphData):
        nodes = {n.id: n for n in graph.nodes}
        # Build adjacency list
        adj = defaultdict(list)
        for e in graph.edges:
            edge = nodes[e.id_a].type.get_edge_by_source_name(e.handle_a)
            if edge.direction == edges.INPUT:
                adj[e.id_a].append(e.id_b)
            else:
                adj[e.id_b].append(e.id_a)

        # Find top level node (no incoming edges)
        all_nodes = set(nodes.keys())
        incoming = set()
        for targets in adj.values():
            incoming.update(targets)
        top_level_nodes = list(all_nodes - incoming)

        if len(top_level_nodes) > 1:
            self.errors.append(DanglingNodeInGraph())

    def _validate_triggers(self, nodes: list[NodeData]):
        triggers = sum(1 for n in nodes if n.type.TRIGGER)
        if triggers != 1:
            self.errors.append(InvalidTriggerNodeCount())


@dataclass
class GraphValidationError:
    pass


@dataclass
class InvalidNodeType(GraphValidationError):
    id: str
    msg: str = field(default="Invalid node type", init=False)


@dataclass
class IdRepeated(GraphValidationError):
    id: str
    msg: str = field(default="Node id is not unique", init=False)


@dataclass
class EdgeWrongID(GraphValidationError):
    start_id: str
    end_id: str
    msg: str = field(default="Edge doesn't connect to existing node", init=False)


@dataclass
class InvalidNodeField(GraphValidationError):
    id: str
    field: str
    msg: str = field(default="Node doesn't have such field", init=False)


@dataclass
class InvalidNodeFieldValue(GraphValidationError):
    id: str
    field: str
    value: str
    msg: str = field(default="Invalid value", init=False)


@dataclass
class NodeNotAllInputsConnected(GraphValidationError):
    id: str
    inputs: list[str]
    msg: str = field(
        default="Node needs to have all of its inputs connected", init=False
    )


@dataclass
class EdgeInvalidHandle(GraphValidationError):
    from_id: str
    to_id: str
    handle: str
    msg: str = field(default="Edge handle doesn't exist on the node", init=False)


@dataclass
class EdgeWrongDirection(GraphValidationError):
    from_id: str
    to_id: str
    msg: str = field(default="Edge must connect from input to output", init=False)


@dataclass
class EdgeTypeMismatchOnEnds(GraphValidationError):
    from_id: str
    to_id: str
    msg: str = field(default="Edge connects two incompatible end", init=False)


@dataclass
class ConnectionDuplicate(GraphValidationError):
    from_id: str
    to_id: str
    msg: str = field(default="There already exists such edge", init=False)


@dataclass
class CycleInGraph(GraphValidationError):
    msg: str = field(default="There is a cycle in this graph", init=False)


@dataclass
class DanglingNodeInGraph(GraphValidationError):
    msg: str = field(default="Not all nodes are connected to each other", init=False)


@dataclass
class InvalidTriggerNodeCount(GraphValidationError):
    msg: str = field(
        default="There must be exactly one trigger node in the graph", init=False
    )
