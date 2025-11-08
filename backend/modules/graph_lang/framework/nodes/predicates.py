from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import Node, ExecutionContext

# ruff: noqa: N815


class IsGreaterLesserNode(Node):
    TYPE_NAME = 'isGreaterLesser'

    inValue = edges.NumberType(direction=edges.INPUT)
    inX = edges.NumberType(direction=edges.INPUT)
    direction = edges.EnumType(
        direction=edges.INPUT, allowed_values=["greater", "less"]
    )

    out = edges.BoolType(direction=edges.OUTPUT)

    def execute(self, context :ExecutionContext):
        direction = self.direction(context)
        value = self.inValue(context)
        x = self.inX(context)

        if direction == "less":
            self.out.set(value < x)
        else:
            self.out.set(value > x)
