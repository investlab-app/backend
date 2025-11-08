from modules.graph_lang.framework import edges
from modules.graph_lang.framework.actions import BuySellAction, GraphActionSet
from modules.graph_lang.framework.nodes.node import Node, ExecutionContext


class BuySellAmountNode(Node):
    TYPE_NAME = "buySellAmount"

    action = edges.EnumType(direction=edges.INPUT, allowed_values=["buy", "sell"])
    amount = edges.NumberType(direction=edges.INPUT)
    ticker = edges.InstrumentType(direction=edges.INPUT)

    out = edges.VoidType(direction=edges.OUTPUT)

    def execute(self, context: ExecutionContext):
        action = BuySellAction(
            action=self.action(context),
            amount=self.amount(context),
            ticker=self.ticker(context),
        )
        context.effects.add(action)

        self.out.set(None)

