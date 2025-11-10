from modules.graph_lang.framework import edges
from modules.graph_lang.framework.actions import BuySellAmountAction
from modules.graph_lang.framework.nodes.node import Node, ExecutionContext


class BuySellAmountNode(Node):
    TYPE_NAME = "buySellAmount"

    action = edges.EnumType(direction=edges.INPUT, allowed_values=["buy", "sell"])
    amount = edges.NumberType(direction=edges.INPUT)
    ticker = edges.InstrumentType(direction=edges.INPUT)

    out = edges.VoidType(direction=edges.OUTPUT)

    def _execute(self, context: ExecutionContext):
        action = self._get(self.action)
        amount = self._get(self.amount)
        ticker = self._get(self.ticker)

        action = BuySellAmountAction(action=action, amount=amount, ticker=ticker)
        context.effects.add(action)

        self.out.set(None)

        context.log(
            self.id,
            "BuySell",
            {
                "action": action,
            },
        )
