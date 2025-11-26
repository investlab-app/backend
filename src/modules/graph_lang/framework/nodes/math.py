from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import ExecutionContext, Node

# ruff: noqa: N815


class AddNode(Node):
    TYPE_NAME = "add"

    inA = edges.NumberType(direction=edges.INPUT)
    inB = edges.NumberType(direction=edges.INPUT)

    out = edges.NumberType(direction=edges.OUTPUT)

    def _execute(self, context: ExecutionContext):
        a = self._get(self.inA)
        b = self._get(self.inB)
        output = a + b

        self.out.set(output)

        context.log(self.id, "Add", fields={"inA": a, "inB": b, "out": output})


class SubtractNode(Node):
    TYPE_NAME = "subtract"

    inA = edges.NumberType(direction=edges.INPUT)
    inB = edges.NumberType(direction=edges.INPUT)

    out = edges.NumberType(direction=edges.OUTPUT)

    def _execute(self, context: ExecutionContext):
        a = self._get(self.inA)
        b = self._get(self.inB)
        output = a - b

        self.out.set(output)

        context.log(self.id, "Subtract", fields={"inA": a, "inB": b, "out": output})


class MultiplyNode(Node):
    TYPE_NAME = "multiply"

    inA = edges.NumberType(direction=edges.INPUT)
    inB = edges.NumberType(direction=edges.INPUT)

    out = edges.NumberType(direction=edges.OUTPUT)

    def _execute(self, context: ExecutionContext):
        a = self._get(self.inA)
        b = self._get(self.inB)
        output = a * b

        self.out.set(output)

        context.log(self.id, "Multiply", fields={"inA": a, "inB": b, "out": output})


class DivideNode(Node):
    TYPE_NAME = "divide"

    inA = edges.NumberType(direction=edges.INPUT)
    inB = edges.NumberType(direction=edges.INPUT)

    out = edges.NumberType(direction=edges.OUTPUT)

    def _execute(self, context: ExecutionContext):
        a = self._get(self.inA)
        b = self._get(self.inB)
        if b == 0:
            raise RuntimeError("Dividend can not be 0!")
        output = a / b

        self.out.set(output)

        context.log(self.id, "Divide", fields={"inA": a, "inB": b, "out": output})


class NumericIfNode(Node):
    TYPE_NAME = "numbericFlowIf"

    inIf = edges.BoolType(direction=edges.INPUT)
    inThen = edges.NumberType(direction=edges.INPUT)
    inElse = edges.NumberType(direction=edges.INPUT)

    out = edges.NumberType(direction=edges.OUTPUT)

    def _execute(self, context: ExecutionContext):
        in_if = self._get(self.inIf)

        output = self._get(self.inThen) if in_if else self._get(self.inElse)
        self.out.set(output)

        context.log(
            self.id,
            "numericIf",
            {"if": in_if, "then" if in_if else "else": output, "output": output},
        )


# TODO add exception handling
