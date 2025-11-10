import json
import pytest
from modules.graph_lang.framework import edges
from modules.graph_lang.framework.builder import GraphBuilder
from modules.graph_lang.framework.nodes import Node
from modules.graph_lang.framework.parser import EdgeData, GraphData, NodeData
from modules.graph_lang.models import Graph
from modules.graph_lang.tests.conftest import fake_graph


class MockTrigger(Node):
    TRIGGER = True

    inVal = edges.VoidType(direction=edges.INPUT, source="input")


class MockNode(Node):
    TRIGGER = True


class MockSplitNode(Node):
    output = edges.VoidType(direction=edges.OUTPUT)

    in_a = edges.BoolType(direction=edges.INPUT, source="source_a")
    in_b = edges.EnumType(direction=edges.INPUT, allowed_values=["a", "b"])
    data = edges.NumberType(direction=edges.INPUT)


class MockBoolOutput(Node):
    output = edges.BoolType(direction=edges.OUTPUT)


class MockEnumOutput(Node):
    output = edges.EnumType(
        direction=edges.OUTPUT, source="hehexd", allowed_values=["a", "b"]
    )


class MockNodeFactory:
    def __init__(self):
        self.types = {}
        self.names = {}

    def from_type(self, type: type[Node]) -> Node:
        return self.types[type]

    def name_to_type(self, name: str) -> type:
        return self.names[name]

    def set_node(self, type_name: str, type: type[Node], node: Node):
        self.names[type_name] = type
        self.types[type] = node


@pytest.mark.django_db
def test_graph_builder():
    node_1 = MockTrigger()
    node_2 = MockSplitNode()
    node_3 = MockBoolOutput()
    node_4 = MockEnumOutput()

    factory = MockNodeFactory()
    factory.set_node("MockTrigger", MockTrigger, node_1)
    factory.set_node("MockSplitNode", MockSplitNode, node_2)
    factory.set_node("MockBoolOutput", MockBoolOutput, node_3)
    factory.set_node("MockEnumOutput", MockEnumOutput, node_4)

    data = GraphData(
        nodes=[
            NodeData(id="1", type="MockTrigger"),
            NodeData(id="2", type="MockSplitNode", fields={"data": "34"}),
            NodeData(id="3", type="MockBoolOutput", fields={"output": "True"}),
            NodeData(id="4", type="MockEnumOutput", fields={"hehexd": "a"}),
        ],
        edges=[
            EdgeData(id_a="1", handle_a="input", id_b="2", handle_b="output"),
            EdgeData(id_a="2", handle_a="source_a", id_b="3", handle_b="output"),
            EdgeData(id_a="2", handle_a="in_b", id_b="4", handle_b="hehexd"),
        ],
    )

    result = GraphBuilder(factory).build(data)

    assert result == node_1
    assert node_1.inVal.output.node == node_2
    assert node_2.in_a.output.node == node_3
    assert node_2.in_b.output.node == node_4


@pytest.mark.django_db
def test_graph_builder__from_db():
    node = MockNode()
    data = GraphData(nodes=[NodeData(id="4", type="MockNode")])
    factory = MockNodeFactory()
    factory.set_node("MockNode", MockNode, node)

    graph = fake_graph(graph_data=data.model_dump(), save=True)

    result = GraphBuilder(factory).get_from_db(graph.id)

    assert result == node


@pytest.mark.django_db
def test_graph_builder__from_db__graph_not_in_db__raises_value_error():
    factory = MockNodeFactory()

    with pytest.raises(ValueError):
        GraphBuilder(factory).get_from_db("doesn`t exist")
