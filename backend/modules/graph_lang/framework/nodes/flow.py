from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import Node, ExecutionContext

# ruff: noqa: N815


class FlowIfNode(Node):
    TYPE_NAME = 'flowIF'

    inIf = edges.BoolType(direction=edges.INPUT)
    inThen = edges.VoidType(direction=edges.INPUT)
    inElse = edges.VoidType(direction=edges.INPUT)

    out = edges.VoidType(direction=edges.OUTPUT)

    def execute(self, context :ExecutionContext):
        if self.inIf(context):
            self.inThen(context)
        else:
            self.inElse(context)
        self.out.set(None)
