from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import ExecutionContext, Node

# ruff: noqa: N815


class FlowIfNode(Node):
    TYPE_NAME = "flowIF"

    inIf = edges.BoolType(direction=edges.INPUT)
    inThen = edges.VoidType(direction=edges.INPUT)
    inElse = edges.VoidType(direction=edges.INPUT)

    out = edges.VoidType(direction=edges.OUTPUT)

    def _execute(self, context: ExecutionContext):
        inIf = self._get(self.inIf)

        if inIf:
            self._get(self.inThen)
        else:
            self._get(self.inElse)
        self.out.set(None)

        context.log(
            self.id,
            "If",
            {
                "if": inIf,
                "then" if inIf else "else": None,
            },
        )
