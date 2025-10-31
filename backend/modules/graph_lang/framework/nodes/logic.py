from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import Node

# ruff: noqa: N815


class AndNode(Node):
    inA = edges.BoolType(direction=edges.INPUT)
    inB = edges.BoolType(direction=edges.INPUT)

    out = edges.BoolType(direction=edges.OUTPUT)

    def execute(self):
        a = self.inA()
        b = self.inB()

        self.out.set(a and b)


class OrNode(Node):
    inA = edges.BoolType(direction=edges.INPUT)
    inB = edges.BoolType(direction=edges.INPUT)

    out = edges.BoolType(direction=edges.OUTPUT)

    def execute(self):
        a = self.inA()
        b = self.inB()

        self.out.set(a or b)


class NotNode(Node):
    inVal = edges.BoolType(direction=edges.INPUT, source="in")
    out = edges.BoolType(direction=edges.OUTPUT)

    def execute(self):
        val = self.inVal()

        self.out.set(not val)
