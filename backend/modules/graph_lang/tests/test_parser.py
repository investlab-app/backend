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


# TODO write test for minimal passing data
class TestParser:
    @pytest.fixture(autouse=True)
    def setup(self):
        self._parser = Parser()

    def test_parse_fails_bad_structure(self):
        json_data = {"invalid": "data"}

        result = self._parser.parse(json_data)

        assert result is None

    def test_parse__node_type_not_in_factory__returns_none_type(self):
        json_data = {
            "nodes": [
                {
                    "id": "1",
                    "type": "A type",
                    "data": {"settings": {}},
                }
            ],
            "edges": [],
        }

        result = self._parser.parse(json_data)

        assert result == GraphData(nodes=[NodeData(id="1", type="A type", fields={})])

    def test_parse__replaces_unit_period_with_timespan(self):
        json_data = {
            "nodes": [
                {
                    "id": "1",
                    "type": "node_type",
                    "data": {"settings": {"unit": "day", "interval": 4}},
                },
            ],
        }

        result = self._parser.parse(json_data)

        assert result == GraphData(
            nodes=[NodeData(id="1", type="node_type", fields={"timespan": "4 day"})]
        )

    def test_parse__test_valid_data(self):
        json_data = {
            "nodes": [
                {"id": "1", "type": "node_type1", "data": {"settings": {}}},
                {
                    "id": "2",
                    "type": "node_type2",
                    "data": {"settings": {"field1": "value"}},
                },
                {
                    "id": "3",
                    "type": "node_type3",
                    "data": {
                        "settings": {
                            "field1": "value1",
                            "field2": "value2",
                            "field3": "value3",
                        }
                    },
                },
            ],
            "edges": [
                {
                    "source": "14",
                    "sourceHandle": "4chan",
                    "target": "1",
                    "targetHandle": "asdf",
                }
            ],
        }

        result = self._parser.parse(json_data)

        assert result == GraphData(
            nodes=[
                NodeData(id="1", type="node_type1", fields={}),
                NodeData(id="2", type="node_type2", fields={"field1": "value"}),
                NodeData(
                    id="3",
                    type="node_type3",
                    fields={
                        "field1": "value1",
                        "field2": "value2",
                        "field3": "value3",
                    },
                ),
            ],
            edges=[EdgeData(id_a="14", handle_a="4chan", id_b="1", handle_b="asdf")],
        )
