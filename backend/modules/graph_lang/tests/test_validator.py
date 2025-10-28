import pytest
from modules.graph_lang.framework.validator import GraphParser
from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import Node
from modules.graph_lang.tests.conftest import EmptyNode, MockNodeFactory, BoolInputNode




class TestParser:

    @pytest.fixture(autouse=True)
    def setup(self):
        self.node_factory = MockNodeFactory()
        self.parser = GraphParser(self.node_factory)
        

    def test_no_nodes__parser_returns_empty_list(self):
        data = {
            'nodes': []
        }

        assert self.parser.parse(data) == []

    def test_single_node__missing_id__raises_parse_error(self):
        data = {
            'nodes': [{
                'type': 'someNodeType'
            }]
        }

        with pytest.raises(ValueError):
            self.parser.parse(data)


    def test_single_node__missing_type__raises_parse_error(self):
        data = {
            'nodes': [{
                'id': 'node_0'
            }]
        }

        with pytest.raises(ValueError):
            self.parser.parse(data)


    def test_single_node__illegal_node_type__raises_parse_error(self):
        data = {
            'nodes': [{
                'id': 'node_0',
                'type': 'theresNoSuchNode',
            }]
        }

        with pytest.raises(ValueError):
            self.parser.parse(data)

    

    def test_single_node__legal_type__returns_node(self):
        node = EmptyNode()
        self.node_factory.nodes['emptyNode'] = node
        data = {
            'nodes': [{
                'id': 'node_0',
                'type': 'emptyNode',
            }]
        }

        assert self.parser.parse(data) == [node]



    def test_single_node__illegal_data_field__raises_parse_error(self):
        node = EmptyNode()
        self.node_factory.nodes['emptyNode'] = node
        data = {
            'nodes': [{
                'id': 'node_0',
                'type': 'emptyNode',
                'data': {'settings': {
                    'should not be here': 'hehexd'
                }}
            }]
        }

        with pytest.raises(ValueError):
            self.parser.parse(data)

    def test_single_node__single_data_field__passes(self):
        class BoolInputNode(Node):
            someData = edges.BoolType(direction=edges.INPUT)

        self.node_factory.nodes['boolInputNode'] = BoolInputNode()
        data = {
            'nodes': [{
                'id': 'node_0',
                'type': 'boolInputNode',
                'data': {'settings': {
                    'someData': 'true'
                }}
            }]
        }

        node = self.parser.parse(data)[0]
        assert node.someData.get_raw_value() == 'true'

    def test_single_node__single_data_field_different_source__passes(self):

        class BoolInputNode(Node):
            someData = edges.BoolType(direction=edges.INPUT, source='surprise')


        self.node_factory.nodes['boolInputNode'] = BoolInputNode()
        data = {
            'nodes': [{
                'id': 'node_0',
                'type': 'boolInputNode',
                'data': {'settings': {
                    'surprise': 'false'
                }}
            }]
        }

        node = self.parser.parse(data)[0]
        assert node.someData.get_raw_value() == 'false'

    def test_single_node__data_as_output_edge__raises_error(self):
        class BoolOutputNode(Node):
            someData = edges.BoolType(direction=edges.OUTPUT)


        self.node_factory.nodes['node_type'] = BoolOutputNode()
        data = {
            'nodes': [{
                'id': 'node_0',
                'type': 'node_type',
                'data': {'settings': {
                    'someData': 'false'
                }}
            }]
        }

        with pytest.raises(ValueError):
            self.parser.parse(data)

    def test_single_node__multiple_data_fields__passes(self):
        class SomeInputNode(Node):
            data_a = edges.BoolType(direction=edges.INPUT, source='hehexd')
            data_b = edges.InstrumentType(direction=edges.INPUT)
            data_c = edges.EnumType(direction=edges.OUTPUT, allowed_values=['a', 'b'])
            data_d = edges.BoolType(direction=edges.INPUT)

        self.node_factory.nodes['node_type'] = SomeInputNode()
        data = {
            'nodes': [{
                'id': 'node_0',
                'type': 'node_type',
                'data': {'settings': {
                    'hehexd': 'false',
                    'data_b': 'first',
                }}
            }]
        }

        node = self.parser.parse(data)[0]

        assert node.data_a.get_raw_value() == 'false'
        assert node.data_b.get_raw_value() == 'first'
        assert node.data_d.get_raw_value() == None
