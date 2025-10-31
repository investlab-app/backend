from collections import defaultdict
from dataclasses import dataclass

from modules.graph_lang.framework import edges
from modules.graph_lang.framework.parser import EdgeData, GraphData, NodeData


class Validator:
    def validate(self, data: GraphData):
        self.errors = []

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

    def _check_node_id_repeats(self, nodes: list[NodeData]):
        node_ids = set()
        for node in nodes:
            if node.id in node_ids:
                self.errors.append(IdRepeated(id=node.id))
            node_ids.add(node.id)

    def _check_node_types(self, nodes: list[NodeData]):
        for node in nodes:
            if not node.type:
                self.errors.append(InvalidNodeType(node.id))

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
                    self.errors.append(InvalidNodeField(node.id, field))

    def _validate_node_field_values(self, nodes: list[NodeData]):
        for node in nodes:
            edges = node.type.get_incoming_edges()

            for field, value in node.fields.items():
                edge = next((e for e in edges if field == e.source_name), None)
                if not edge:
                    return
                if not edge.validate_value(value):
                    self.errors.append(InvalidNodeFieldValue(node.id, field, value))

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


@dataclass(frozen=True)
class InvalidNodeType:
    id: str


@dataclass(frozen=True)
class IdRepeated:
    id: str


@dataclass(frozen=True)
class EdgeWrongID:
    start_id: str
    end_id: str


@dataclass(frozen=True)
class InvalidNodeField:
    id: str
    field: str


@dataclass(frozen=True)
class InvalidNodeFieldValue:
    id: str
    field: str
    value: str


@dataclass(frozen=True)
class NodeNotAllInputsConnected:
    id: str
    inputs: list[str]


@dataclass(frozen=True)
class EdgeInvalidHandle:
    from_id: str
    to_id: str
    handle: str


@dataclass(frozen=True)
class EdgeWrongDirection:
    from_id: str
    to_id: str


@dataclass(frozen=True)
class EdgeTypeMismatchOnEnds:
    from_id: str
    to_id: str


@dataclass(frozen=True)
class ConnectionDuplicate:
    from_id: str
    to_id: str


@dataclass(frozen=True)
class CycleInGraph:
    pass


@dataclass(frozen=True)
class DanglingNodeInGraph:
    pass


@dataclass(frozen=True)
class InvalidTriggerNodeCount:
    pass
