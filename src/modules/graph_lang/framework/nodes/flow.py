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
        in_if = self._get(self.inIf)

        if in_if:
            self._get(self.inThen)
        else:
            self._get(self.inElse)
        self.out.set(None)

        context.log(
            self.id,
            "If",
            {
                "if": in_if,
                "then" if in_if else "else": None,
            },
        )

    @classmethod
    def validate_all_needed_edges(cls, edges):
        if cls.inIf in edges:
            return cls.inThen in edges or cls.inElse in edges
        return False
