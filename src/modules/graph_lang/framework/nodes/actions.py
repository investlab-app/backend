from modules.graph_lang.framework import edges
from modules.graph_lang.framework.actions import (
    BuySellAmountAction,
    BuySellForPriceAction,
    BuySellPercentAction,
    NotificationAction,
)
from modules.graph_lang.framework.nodes.node import ExecutionContext, Node


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


class BuySellPriceNode(Node):
    TYPE_NAME = "buySellPrice"

    action = edges.EnumType(direction=edges.INPUT, allowed_values=["buy", "sell"])
    ticker = edges.InstrumentType(direction=edges.INPUT)
    price = edges.NumberType(direction=edges.INPUT)

    out = edges.VoidType(direction=edges.OUTPUT)

    def _execute(self, context: ExecutionContext):
        action = self._get(self.action)
        ticker = self._get(self.ticker)
        price = self._get(self.price)

        effect = BuySellForPriceAction(action=action, ticker=ticker, price=price)
        context.effects.add(effect)

        self.out.set(None)

        context.log(self.id, "BuySellPrice", {"action": effect})


class BuySellPercentNode(Node):
    TYPE_NAME = "buySellPercent"

    action = edges.EnumType(direction=edges.INPUT, allowed_values=["buy", "sell"])
    percent = edges.NumberType(direction=edges.INPUT)
    ticker = edges.InstrumentType(direction=edges.INPUT)

    out = edges.VoidType(direction=edges.OUTPUT)

    def _execute(self, context: ExecutionContext):
        action = self._get(self.action)
        percent = self._get(self.percent)
        ticker = self._get(self.ticker)

        effect = BuySellPercentAction(action=action, percent=percent, ticker=ticker)
        context.effects.add(effect)

        self.out.set(None)

        context.log(self.id, "BuySellPercent", {"action": effect})


class SendNotificationNode(Node):
    TYPE_NAME = "sendNotification"

    format = edges.EnumType(direction=edges.INPUT, allowed_values=["push", "email"])
    message = edges.StringType(direction=edges.INPUT)

    out = edges.VoidType(direction=edges.OUTPUT)

    def _execute(self, context: ExecutionContext):
        fmt = self._get(self.format)
        msg = self._get(self.message)

        effect = NotificationAction(format=fmt, message=msg)
        context.effects.add(effect)

        self.out.set(None)

        context.log(self.id, "SendNotification", {"notification": effect})
