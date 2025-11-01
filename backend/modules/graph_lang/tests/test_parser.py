from typing import Optional
import pytest

from modules.graph_lang.framework.parser import (
    Parser,
    GraphData,
    NodeData,
    EdgeData,
    NodeFactory,
    Node,
)


class MockType:
    pass


class MockFactory:
    def __init__(self):
        self.types = {}

    def name_to_type(self, name: str) -> Optional[type[Node]]:
        return self.types.get(name, None)

    def register_type(self, name: str, type: type):
        self.types[name] = type


# TODO write test for minimal passing data
class TestParser:
    def __init__(self):
        self._mock_factory = MockFactory()
        self._parser = Parser(self._mock_factory)

    def test_parse_fails_bad_structure(self):
        json_data = {"invalid": "data"}

        result = self._parser.parse(json_data)

        assert result is None

    def test_parse__node_type_not_in_factory__returns_none_type(self):
        json_data = {
            "nodes": [
                {
                    "id": "1",
                    "type": "UnknownNode",
                    "settings": {"data": []},
                }
            ],
            "edges": [],
        }

        result = self._parser.parse(json_data)

        assert result == GraphData(nodes=[NodeData(id="1", type=None, fields={})])

    def test_parse__valid_node_type(self):
        self._mock_factory.register_type("ValidNode", MockType)
        json_data = {
            "nodes": [{"id": "1", "type": "ValidNode", "settings": {"data": []}}],
        }

        result = self._parser.parse(json_data)

        assert result == GraphData(nodes=[NodeData(id="1", type=MockType, fields={})])

    def test_parse__test_valid_data(self):
        self._mock_factory.register_type("ValidNode", MockType)
        json_data = {
            "nodes": [
                {"id": "1", "type": "ValidNode", "settings": {"data": []}},
                {
                    "id": "2",
                    "type": "ValidNode",
                    "settings": {"data": {"field1": "value"}},
                },
                {
                    "id": "3",
                    "type": "InvalidNode",
                    "settings": {
                        "data": {
                            "field1": "value1",
                            "field2": "value2",
                            "field3": "value3",
                        }
                    },
                },
            ],
            "edges": [
                {
                    'source': '14',
                    'source_handle': '4chan',
                    "target": '1',
                    "target_handle": 'asdf'
                }
            ]
        }

        result = self._parser.parse(json_data)

        assert result == GraphData(
            nodes=[
                NodeData(id='1', type=MockType, fields={}),
                NodeData(id='2', type=MockType, fields={'field1': 'value'}),
                NodeData(id='3', type=None, fields={
                    "field1": "value1",
                    "field2": "value2",
                    "field3": "value3",
                }),
            ],
            edges=[
                EdgeData('14', '4chan', '1', 'asdf')
            ]
        )
        assert False
