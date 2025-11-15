from modules.graph_lang.framework.nodes import Node, NodeFactory
from modules.graph_lang.framework.nodes.node import NodeInput
from modules.graph_lang.framework.parser import GraphData
from modules.graph_lang.models import Graph


class GraphBuilder:
    def __init__(self, node_factory: NodeFactory = None):
        self.factory = node_factory or NodeFactory()

    def build(self, validated_data: GraphData) -> Node:
        nodes: dict[str, Node] = {}

        for node_data in validated_data.nodes:
            node_type = self.factory.name_to_type(node_data.type)
            node = self.factory.from_type(node_type)
            node.id = node_data.id
            nodes[node.id] = node

            for field, value in node_data.fields.items():
                parsed = type(node).get_edge_by_source_name(field).parse(value)
                node.get_io_by_source_name(field).set(parsed)

        for edge in validated_data.edges:
            node_a = nodes[edge.id_a]
            node_b = nodes[edge.id_b]

            in_a = node_a.get_io_by_source_name(edge.handle_a)
            in_b = node_b.get_io_by_source_name(edge.handle_b)

            if isinstance(in_a, NodeInput):
                in_a.connect(in_b)
            else:
                in_b.connect(in_a)

        trigger = next(node for node in nodes.values() if node.TRIGGER)
        return trigger

    def get_from_db(self, graph_id):
        try:
            graph = Graph.objects.get(id=graph_id)
        except:
            raise ValueError("Specified graph does not exist")

        graph_data = GraphData.model_validate(graph.graph_data)
        return self.build(graph_data)
