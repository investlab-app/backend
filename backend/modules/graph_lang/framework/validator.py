from modules.graph_lang.framework.nodes.node import Node
from modules.graph_lang.framework import edges
import itertools


class GraphParser:

    def __init__(self, factory = None):
        self.factory = factory

    def parse(self, data :dict) -> list[Node]:
        nodes = [
            self.parse_node_data(node_data)
            for node_data in data['nodes']
        ]
        return nodes

    def parse_node_data(self, node_data :dict) -> Node:
        self.check_for_required_fields_on_node(node_data)
        node = self.try_create_node(node_data)

        if 'data' in node_data and 'settings' in node_data['data']:
            self.parse_data_fields(node_data['data']['settings'], node)

        return node

    def parse_data_fields(self, data_fields :dict, node :Node):
        for data_field in data_fields:

            node_field = next((
                getattr(node, edge.field_name)
                for edge in node.all_edges
                if edge.direction == edges.INPUT and data_field == edge.source_name
            ), None)

            if not node_field:
                raise ValueError(f'Node {node.id} has illegal data field {data_field}')

            node_field.set_raw_value(data_fields[data_field])

    def check_for_required_fields_on_node(self, node_data :dict):
        if not 'id' in node_data:
            raise ValueError('Node missing id')
        if not 'type' in node_data:
            raise ValueError(f'Node {node_data['id']} is missing its type')

    def try_create_node(self, node_data :dict):
        try:
            node = self.factory.create_from_type(node_data['type'])
            node.id = node_data['id']
            return node
        except:
            raise ValueError(f'Node {node_data['id']} has invalid type')

