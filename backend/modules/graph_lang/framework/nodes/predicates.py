from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import Node

# ruff: noqa: N815


class IsGreaterLesserNode(Node):
    TYPE_NAME = 'isGreaterLesser'

    inValue = edges.NumberType(direction=edges.INPUT)
    inX = edges.NumberType(direction=edges.INPUT)
    direction = edges.EnumType(
        direction=edges.INPUT, allowed_values=["greater", "lesser"]
    )

    out = edges.BoolType(direction=edges.OUTPUT)

    def execute(self):
        direction = self.direction()
        value = self.inValue()
        x = self.inX()

        if direction == "lesser":
            self.out.set(value < x)
        else:
            self.out.set(value > x)
