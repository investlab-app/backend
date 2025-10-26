from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import Node

# ruff: noqa: N815


class FlowIfNode(Node):
    inIf = edges.BoolType(direction=edges.INPUT)
    inThen = edges.VoidType(direction=edges.INPUT)
    inElse = edges.VoidType(direction=edges.INPUT)

    out = edges.VoidType(direction=edges.OUTPUT)

    def execute(self):
        if self.inIf():
            self.inThen()
        else:
            self.inElse()
        self.out.set(None)
