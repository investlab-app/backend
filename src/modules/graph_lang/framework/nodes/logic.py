from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import ExecutionContext, Node

# ruff: noqa: N815


class AndNode(Node):
    TYPE_NAME = "and"

    inA = edges.BoolType(direction=edges.INPUT)
    inB = edges.BoolType(direction=edges.INPUT)

    out = edges.BoolType(direction=edges.OUTPUT)

    def _execute(self, context: ExecutionContext):
        a = self._get(self.inA)
        b = self._get(self.inB)
        output = a and b

        self.out.set(output)

        context.log(self.id, "And", {"a": a, "b": b, "out": output})


class OrNode(Node):
    TYPE_NAME = "or"

    inA = edges.BoolType(direction=edges.INPUT)
    inB = edges.BoolType(direction=edges.INPUT)

    out = edges.BoolType(direction=edges.OUTPUT)

    def _execute(self, context: ExecutionContext):
        a = self._get(self.inA)
        b = self._get(self.inB)
        output = a or b

        self.out.set(output)

        context.log(self.id, "or", {"a": a, "b": b, "out": output})


class NotNode(Node):
    TYPE_NAME = "not"

    inVal = edges.BoolType(direction=edges.INPUT, source="in")
    out = edges.BoolType(direction=edges.OUTPUT)

    def _execute(self, context: ExecutionContext):
        val = self._get(self.inVal)
        output = not val

        self.out.set(output)

        context.log(self.id, "not", {"in": val, "out": output})


# class OccuredXTimesNode(Node):
#     TYPE_NAME = 'occuredXTimes'
#     SAMPLES = 25

#     inVal = edges.BoolType(direction=edges.INPUT, source = 'in')
#     times = edges.NumberType(direction=edges.INPUT)


#     out = edges.BoolType(direction=edges.OUTPUT)

#     def _execute(self, context):
#         return super()._execute(context)
