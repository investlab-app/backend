import pytest

from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes import Node
from modules.graph_lang.framework.validator import *
from modules.graph_lang.framework.validator import EdgeData, GraphData, NodeData
from modules.graph_lang.tests.conftest_nodes import (
    EmptyNode,
    EnumInputNode,
    NumberInputChangeSourceNode,
    NumberInputNode,
    NumberInputOutputNode,
    NumberOutputNode,
    TriggerNode,
    TwoBoolInputNode,
    TypeMismatchNode,
)


class NodeFactory:
    def __init__(self):
        self.types = {}

    def name_to_type(self, name) -> type:
        return self.types[name]

    def type_exists(self, name) -> bool:
        return name in self.types

    def set_type(self, name, type_):
        self.types[name] = type_


class TestValidator:
    @pytest.fixture(autouse=True)
    def setup(self):
        factory = NodeFactory()
        factory.set_type("EmptyNode", EmptyNode)
        factory.set_type("EnumInputNode", EnumInputNode)
        factory.set_type("NumberInputChangeSourceNode", NumberInputChangeSourceNode)
        factory.set_type("NumberInputNode", NumberInputNode)
        factory.set_type("NumberInputOutputNode", NumberInputOutputNode)
        factory.set_type("NumberOutputNode", NumberOutputNode)
        factory.set_type("TriggerNode", TriggerNode)
        factory.set_type("TwoBoolInputNode", TwoBoolInputNode)
        factory.set_type("TypeMismatchNode", TypeMismatchNode)
        self.validator = Validator(factory)

    def run(self, data):
        return self.validator.validate(data)

    def error_absent(self, error, error_set):
        return not any(isinstance(x, error) for x in error_set)

    def test__invalid_node_type__returns_invalid_type_error(self):
        errors = self.run(
            GraphData(
                nodes=[
                    NodeData(id="0", type="invalid"),
                    NodeData(id="1", type="EmptyNode"),
                ]
            )
        )

        assert InvalidNodeType(id="0") in errors
        assert InvalidNodeType(id="1") not in errors

    def test__node_id_repeated__returns_id_repeated(self):
        data = GraphData(
            nodes=[
                NodeData(id="0", type="EmptyNode"),
                NodeData(id="0", type="EmptyNode"),
            ]
        )
        errors = self.run(data)
        assert IdRepeated(id="0") in errors

    def test__edge_connected_to_invalid_id__returns_edge_wrong_id(self):
        data = GraphData(
            nodes=[NodeData(id="0", type="EmptyNode")],
            edges=[
                EdgeData(id_a="0", handle_a="a", id_b="1", handle_b="b"),
                EdgeData(id_a="2", handle_a="a", id_b="0", handle_b="b"),
            ],
        )
        errors = self.run(data)
        assert EdgeWrongID(start_id="0", end_id="1") in errors
        assert EdgeWrongID(start_id="2", end_id="0") in errors

    def test__node_has_invalid_field__returns_invalid_node_field(self):
        data = GraphData(
            nodes=[NodeData(id="0", type="EmptyNode", fields={"invalid": "hehexd"})]
        )
        errors = self.run(data)
        assert InvalidNodeField("0", "invalid") in errors

    def test__invalid_node_field_value(self):
        data = GraphData(
            nodes=[NodeData(id="0", type="EnumInputNode", fields={"value": "invalid"})]
        )
        errors = self.run(data)
        assert InvalidNodeFieldValue("0", "value", "invalid") in errors

    def test__valid_node_field_value(self):
        data = GraphData(
            nodes=[NodeData(id="0", type="EnumInputNode", fields={"value": "valid1"})]
        )
        errors = self.run(data)
        assert self.error_absent(InvalidNodeFieldValue, errors)

    def test__not_all_inputs_connected(self):
        data = GraphData(
            nodes=[NodeData(id="0", type="TwoBoolInputNode", fields={"inA": "False"})]
        )
        errors = self.run(data)

        assert NodeNotAllInputsConnected("0", ["inB"]) in errors

    def test__edge_invalid_handle(self):
        data = GraphData(
            nodes=[
                NodeData(id="0", type="NumberInputNode"),
                NodeData(id="1", type="NumberOutputNode"),
            ],
            edges=[
                EdgeData(id_a="0", handle_a="illegal_1", id_b="1", handle_b="illegal_2")
            ],
        )
        errors = self.run(data)

        assert EdgeInvalidHandle("0", "1", "illegal_1") in errors
        assert EdgeInvalidHandle("0", "1", "illegal_2") in errors

    def test__edge_direction__allows_only_in_to_out_connections(self):
        data = GraphData(
            nodes=[
                NodeData(id="0", type="NumberInputNode"),
                NodeData(id="1", type="NumberInputNode"),
                NodeData(id="2", type="NumberOutputNode"),
                NodeData(id="3", type="NumberOutputNode"),
            ],
            edges=[
                EdgeData(id_a="0", handle_a="number", id_b="1", handle_b="number"),
                EdgeData(id_a="2", handle_a="number", id_b="3", handle_b="number"),
                EdgeData(id_a="2", handle_a="number", id_b="1", handle_b="number"),
                EdgeData(id_a="1", handle_a="number", id_b="2", handle_b="number"),
            ],
        )
        errors = self.run(data)

        assert EdgeWrongDirection("0", "1") in errors
        assert EdgeWrongDirection("2", "3") in errors
        assert EdgeWrongDirection("2", "1") not in errors
        assert EdgeWrongDirection("1", "2") not in errors

    def test__edge_mismatch(self):
        data = GraphData(
            nodes=[
                NodeData(id="0", type="NumberOutputNode"),
                NodeData(id="1", type="NumberOutputNode"),
                NodeData(id="2", type="TypeMismatchNode"),
            ],
            edges=[
                EdgeData(id_a="2", handle_a="match_val", id_b="0", handle_b="number"),
                EdgeData(
                    id_a="2", handle_a="mismatch_val", id_b="1", handle_b="number"
                ),
            ],
        )
        errors = self.run(data)

        assert EdgeTypeMismatchOnEnds("2", "0") not in errors
        assert EdgeTypeMismatchOnEnds("2", "1") in errors

    def test__connection_duplicate(self):
        data = GraphData(
            nodes=[
                NodeData(id="0", type="NumberOutputNode"),
                NodeData(id="1", type="NumberInputNode"),
                NodeData(id="2", type="NumberInputNode"),
                NodeData(id="3", type="NumberInputNode"),
            ],
            edges=[
                EdgeData(id_a="0", handle_a="number", id_b="1", handle_b="number"),
                EdgeData(id_a="1", handle_a="number", id_b="0", handle_b="number"),
                EdgeData(id_a="0", handle_a="number", id_b="2", handle_b="number"),
                EdgeData(id_a="0", handle_a="number", id_b="3", handle_b="number"),
                EdgeData(id_a="0", handle_a="number", id_b="3", handle_b="number"),
            ],
        )
        errors = self.run(data)

        assert ConnectionDuplicate("0", "1") in errors
        assert ConnectionDuplicate("1", "0") in errors
        assert ConnectionDuplicate("0", "3") in errors

        assert ConnectionDuplicate("3", "0") not in errors
        assert ConnectionDuplicate("0", "2") not in errors
        assert ConnectionDuplicate("2", "0") not in errors

    def test__cycles(self):
        data = GraphData(
            nodes=[
                NodeData(id="0", type="NumberInputOutputNode"),
                NodeData(id="1", type="NumberInputOutputNode"),
                NodeData(id="2", type="NumberInputOutputNode"),
                NodeData(id="3", type="NumberInputOutputNode"),
            ],
            edges=[
                EdgeData(id_a="0", handle_a="inVal", id_b="1", handle_b="outVal"),
                EdgeData(id_a="1", handle_a="inVal", id_b="2", handle_b="outVal"),
                EdgeData(id_a="2", handle_a="inVal", id_b="3", handle_b="outVal"),
                EdgeData(id_a="3", handle_a="inVal", id_b="0", handle_b="outVal"),
            ],
        )
        errors = self.run(data)

        assert CycleInGraph() in errors

    def test_dangling_nodes(self):
        data = GraphData(
            nodes=[
                NodeData(id="0", type="NumberOutputNode"),
                NodeData(id="1", type="NumberInputNode"),
                NodeData(id="2", type="NumberOutputNode"),
            ],
            edges=[
                EdgeData(id_a="0", handle_a="number", id_b="1", handle_b="number"),
            ],
        )
        errors = self.run(data)

        assert DanglingNodeInGraph() in errors

    @pytest.mark.parametrize(
        "no_triggers, raises_error",
        [
            (0, True),
            (1, False),
            (2, True),
        ],
    )
    def test_number_of_triggers(self, no_triggers, raises_error):
        data = GraphData(
            nodes=[NodeData(id=str(i), type="TriggerNode") for i in range(no_triggers)],
        )
        errors = self.run(data)

        if raises_error:
            assert InvalidTriggerNodeCount() in errors
        else:
            assert InvalidTriggerNodeCount() not in errors

    def test_custom_source(self):
        data = GraphData(
            nodes=[
                NodeData(id="1", type="NumberInputChangeSourceNode"),
                NodeData(
                    id="2", type="NumberInputChangeSourceNode", fields={"inVal": "3"}
                ),
                NodeData(id="3", type="NumberOutputNode"),
            ],
            edges=[EdgeData(id_a="1", handle_a="inVal", id_b="3", handle_b="number")],
        )

        errors = self.run(data)

        assert self.error_absent(EdgeInvalidHandle, errors)
        assert self.error_absent(InvalidNodeField, errors)
