from decimal import Decimal

from faker import Faker

from modules.graph_lang.framework.actions import (
    BuySellAmountAction,
    BuySellForPriceAction,
    BuySellPercentAction,
    NotificationAction,
)
from modules.graph_lang.framework.nodes import (
    BuySellAmountNode,
    BuySellPercentNode,
    BuySellPriceNode,
    SendNotificationNode,
)
from modules.graph_lang.framework.nodes.node import ExecutionContext

fake = Faker()


def test_buy_sell_amount_node():
    action_set = set()
    node = BuySellAmountNode()
    node.action.set("buy")
    node.amount.set(25)
    node.ticker.set("AAPL")

    context = ExecutionContext(None, action_set, fake.date_time())
    node.execute(context)

    assert action_set == {BuySellAmountAction("buy", Decimal(25), "AAPL")}


def test_buy_sell_price_node():
    action_set = set()
    node = BuySellPriceNode()
    node.action.set("sell")
    node.ticker.set("GOOG")
    node.price.set(1500)

    context = ExecutionContext(None, action_set, fake.date_time())
    node.execute(context)

    assert action_set == {BuySellForPriceAction("sell", Decimal(1500), "GOOG")}


def test_buy_sell_percent_node():
    action_set = set()
    node = BuySellPercentNode()
    node.action.set("buy")
    node.percent.set(10)
    node.ticker.set("MSFT")

    context = ExecutionContext(None, action_set, fake.date_time())
    node.execute(context)

    assert action_set == {BuySellPercentAction("buy", Decimal(10), "MSFT")}


def test_send_notification_node():
    action_set = set()
    node = SendNotificationNode()
    node.format.set("push")
    node.message.set("Threshold reached")

    context = ExecutionContext(None, action_set, fake.date_time())
    node.execute(context)

    assert action_set == {NotificationAction("push", "Threshold reached")}
