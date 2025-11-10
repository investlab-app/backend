from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import Node, ExecutionContext


class CheckEveryNode(Node):
    TYPE_NAME = "checkEvery"
    TRIGGER = True

    timespan = edges.TimespanType(direction=edges.INPUT)

    in_ = edges.VoidType(direction=edges.INPUT, source="in")

    def _execute(self, context: ExecutionContext):
        self._get(self.in_)

        context.log(self.id, "Check every trigger")


class BoughtSoldNode(Node):
    TYPE_NAME = "boughtSold"
    TRIGGER = True

    ticker = edges.InstrumentType(direction=edges.INPUT)
    action = edges.EnumType(direction=edges.INPUT, allowed_values=["bought", "sold"])

    in_ = edges.VoidType(direction=edges.INPUT, source="in")

    def _execute(self, context: ExecutionContext):
        self._get(self.in_)

        context.log(self.id, "Bought sold trigger")


class PriceTriggerNode(Node):
    TYPE_NAME = "boughtSold"
    TRIGGER = True

    ticker = edges.InstrumentType(direction=edges.INPUT)
    price = edges.NumberType(direction=edges.INPUT)
    direction = edges.EnumType(direction=edges.INPUT, allowed_values=["over", "under"])

    in_ = edges.VoidType(direction=edges.INPUT, source="in")

    def _execute(self, context: ExecutionContext):
        self._get(self.in_)

        context.log(self.id, "Price Trigger")
