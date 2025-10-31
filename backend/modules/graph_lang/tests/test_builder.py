from modules.graph_lang.framework import edges
from modules.graph_lang.framework.builder import GraphBuilder
from modules.graph_lang.framework.nodes import Node
from modules.graph_lang.framework.parser import EdgeData, GraphData, NodeData


class MockTrigger(Node):
    TRIGGER = True

    inVal = edges.VoidType(direction=edges.INPUT, source="input")


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
        self.vals = {}

    def from_type(self, type: type[Node]) -> Node:
        return self.vals[type]

    def set_node(self, type: type[Node], node: Node):
        self.vals[type] = node


def test_graph_builder():
    node_1 = MockTrigger()
    node_2 = MockSplitNode()
    node_3 = MockBoolOutput()
    node_4 = MockEnumOutput()

    factory = MockNodeFactory()
    factory.set_node(MockTrigger, node_1)
    factory.set_node(MockSplitNode, node_2)
    factory.set_node(MockBoolOutput, node_3)
    factory.set_node(MockEnumOutput, node_4)

    data = GraphData(
        nodes=[
            NodeData(id="1", type=MockTrigger),
            NodeData(id="2", type=MockSplitNode, fields={"data": "34"}),
            NodeData(id="3", type=MockBoolOutput, fields={"output": "True"}),
            NodeData(id="4", type=MockEnumOutput, fields={"hehexd": "a"}),
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

    assert node_2.in_a() == True
    assert node_2.data() == 34
    assert node_3.output.get() == True
    assert node_4.output.get() == "a"
