from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import Node, ExecutionContext

# ruff: noqa: N815


class IsGreaterLesserNode(Node):
    TYPE_NAME = "isGreaterLesser"

    inValue = edges.NumberType(direction=edges.INPUT)
    inX = edges.NumberType(direction=edges.INPUT)
    direction = edges.EnumType(
        direction=edges.INPUT, allowed_values=["greater", "less"]
    )

    out = edges.BoolType(direction=edges.OUTPUT)

    def _execute(self, context: ExecutionContext):
        direction = self._get(self.direction)
        value = self._get(self.inValue)
        x = self._get(self.inX)

        if direction == "less":
            output = value < x
        else:
            output = value > x

        self.out.set(output)

        context.log(self.id, direction, {"inVal": value, "x": x, "output": output})
