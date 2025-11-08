from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import Node, ExecutionContext

# ruff: noqa: N815


class AndNode(Node):
    TYPE_NAME = 'and'

    inA = edges.BoolType(direction=edges.INPUT)
    inB = edges.BoolType(direction=edges.INPUT)

    out = edges.BoolType(direction=edges.OUTPUT)

    def execute(self, context :ExecutionContext):
        a = self.inA(context)
        b = self.inB(context)

        self.out.set(a and b)


class OrNode(Node):
    TYPE_NAME = 'or'

    inA = edges.BoolType(direction=edges.INPUT)
    inB = edges.BoolType(direction=edges.INPUT)

    out = edges.BoolType(direction=edges.OUTPUT)



    def execute(self, context :ExecutionContext):
        a = self.inA(context)
        b = self.inB(context)

        self.out.set(a or b)


class NotNode(Node):
    TYPE_NAME = 'not'

    inVal = edges.BoolType(direction=edges.INPUT, source="in")
    out = edges.BoolType(direction=edges.OUTPUT)

    def execute(self, context :ExecutionContext):
        val = self.inVal(context)

        self.out.set(not val)
