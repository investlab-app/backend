from decimal import Decimal

import pytest
from faker import Faker

from modules.graph_lang.framework.actions import BuySellAction, GraphActionSet
from modules.graph_lang.framework.nodes import (
    AndNode,
    BuySellAmountNode,
    ChangeOverTimeNode,
    CheckEveryNode,
    FlowIfNode,
    IsGreaterLesserNode,
    NotNode,
    OrNode,
    PriceOfNode,
)
from modules.graph_lang.tests.conftest_nodes import (
    NumberBasedOnTimeNode,
    PassNumberNode,
    PriceProviderMock,
    VoidSensorNode,
)

fake = Faker()


@pytest.mark.parametrize(
    "in_a, in_b, expected",
    [
        (False, False, False),
        (False, True, False),
        (True, False, False),
        (True, True, True),
    ],
)
def test_and_node(in_a, in_b, expected):
    node = AndNode()
    node.inA.set(in_a)
    node.inB.set(in_b)

    assert node.out.get() == expected


@pytest.mark.parametrize(
    "in_a, in_b, expected",
    [
        (False, False, False),
        (False, True, True),
        (True, False, True),
        (True, True, True),
    ],
)
def test_or_node(in_a, in_b, expected):
    node = OrNode()
    node.inA.set(in_a)
    node.inB.set(in_b)

    assert node.out.get() == expected


@pytest.mark.parametrize(
    "in_val, expected",
    [
        (False, True),
        (True, False),
    ],
)
def test_not_node(in_val, expected):
    node = NotNode()
    node.inVal.set(in_val)

    assert node.out.get() == expected


@pytest.mark.parametrize(
    "in_value, in_x, expected",
    [
        (5, 3, True),
        (-12, 4, False),
        (0, 0, False),
    ],
)
def test_greater_lesser_node__greater(in_value, in_x, expected):
    node = IsGreaterLesserNode()
    node.inValue.set(in_value)
    node.inX.set(in_x)
    node.direction.set("greater")

    assert node.out.get() == expected


@pytest.mark.parametrize(
    "in_value, in_x, expected",
    [
        (-12, 4, True),
        (5, 3, False),
        (7, 7, False),
    ],
)
def test_greater_lesser_node_lesser(in_value, in_x, expected):
    node = IsGreaterLesserNode()
    node.inValue.set(in_value)
    node.inX.set(in_x)
    node.direction.set("less")

    assert node.out.get() == expected


@pytest.mark.parametrize(
    "if_value, then_executed, else_executed",
    [
        (True, True, False),
        (False, False, True),
    ],
)
def test_flow_if_node(if_value, then_executed, else_executed):
    node = FlowIfNode()
    then_node = VoidSensorNode()
    else_node = VoidSensorNode()
    node.inIf.set(if_value)
    node.inThen.connect(then_node.out)
    node.inElse.connect(else_node.out)

    assert node.out.get() is None
    assert then_node.executed == then_executed
    assert else_node.executed == else_executed


def test_change_over_time_node():
    node = ChangeOverTimeNode()
    number_node = NumberBasedOnTimeNode()
    dt_1 = fake.date_time()
    dt_2 = fake.date_time_between(start_date=dt_1)
    number_node.set_val(3, dt_1)
    number_node.set_val(10, dt_2)

    node.timespan.set(dt_2 - dt_1)
    node.in_.connect(number_node.out)
    node.set_execution_time(dt_2)

    assert node.out.get() == 10 - 3


def test_change_over_time__execution_time_not_given__raises_runtime_error():
    node = ChangeOverTimeNode()
    dt_1 = fake.date_time()
    dt_2 = fake.date_time_between(start_date=dt_1)

    node.timespan.set(dt_2 - dt_1)
    node.in_.set(10)

    with pytest.raises(RuntimeError):
        node.out.get()


def test_check_every_node():
    node = CheckEveryNode()
    void_sensor_node = VoidSensorNode()
    node.in_.connect(void_sensor_node.out)

    node.execute()

    assert void_sensor_node.executed is True


def test_buy_sell_amount_node():
    action_set = GraphActionSet()
    trigger_node = CheckEveryNode()
    node = BuySellAmountNode(action_set)
    node.action.set("buy")
    node.amount.set(25)
    node.ticker.set("AAPL")
    trigger_node.in_.connect(node.out)

    trigger_node.execute()

    assert action_set.get_actions() == {BuySellAction("buy", Decimal(25), "AAPL")}


def test_price_of_node():
    dt = fake.date_time()
    price_provider = PriceProviderMock()
    price_provider.set("AAPL", dt, Decimal(10))

    node = PriceOfNode(price_provider)
    node.ticker.set("AAPL")
    node.set_execution_time(dt)

    assert node.out.get() == 10


def test_price_of_node__execution_time_not_given__raises_runtime_error():
    price_provider = PriceProviderMock()

    node = PriceOfNode(price_provider)
    node.ticker.set("AAPL")

    with pytest.raises(RuntimeError):
        node.out.get()


def test_node__execution_time_gets_auto_propagated():
    node_1 = PassNumberNode()
    node_2 = PassNumberNode()
    node_3 = PassNumberNode()
    node_4 = NumberBasedOnTimeNode()

    node_1.in_.connect(node_2.out)
    node_2.in_.connect(node_3.out)
    node_3.in_.connect(node_4.out)

    dt_1 = fake.date_time()
    dt_2 = fake.date_time()

    node_4.set_val(1, dt_1)
    node_4.set_val(2, dt_2)

    node_1.set_execution_time(dt_2)

    assert node_1.out.get() == 2
