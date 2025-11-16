from datetime import timedelta

import pytest
from faker import Faker

from modules.graph_lang.framework.nodes import (
    IsGreaterLesserNode,
    ValueRisenFallenNode,
    ValueStaysAboveBelowNode,
    ValueStaysTheSameNode,
)
from modules.graph_lang.framework.nodes.node import ExecutionContext
from modules.graph_lang.tests.conftest_nodes import MockNumberNode

fake = Faker()


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

    context = ExecutionContext(None, set(), fake.date_time())

    assert node.out.get(context) == expected


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

    context = ExecutionContext(None, set(), fake.date_time())

    assert node.out.get(context) == expected


class TestValueStaysTheSame:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.mock = MockNumberNode()
        self.node = ValueStaysTheSameNode()
        self.node.SAMPLES = 3
        self.node.timespan.set(timedelta(days=2))
        self.node.tolerance.set(10)
        self.node.inVal.connect(self.mock.out)

    @pytest.fixture()
    def dt(self):
        return fake.date_time()

    def test_value_stays_the_same__stays_the_same(self, dt):
        self.mock.set_value(50, dt - timedelta(days=2))
        self.mock.set_value(60, dt - timedelta(days=1))
        self.mock.set_value(40, dt - timedelta(days=0))

        context = ExecutionContext(None, set(), dt)

        assert self.node.out.get(context) is True

    def test__value_outside_tolerance_at_last_tick__out_is_false(self, dt):
        self.mock.set_value(50, dt - timedelta(days=2))
        self.mock.set_value(60, dt - timedelta(days=1))
        self.mock.set_value(61, dt - timedelta(days=0))

        context = ExecutionContext(None, set(), dt)

        assert self.node.out.get(context) is False

    def test__value_outside_tolerance_in_the_middle__out_is_false(self, dt):
        self.mock.set_value(50, dt - timedelta(days=2))
        self.mock.set_value(39, dt - timedelta(days=1))
        self.mock.set_value(50, dt - timedelta(days=0))

        context = ExecutionContext(None, set(), dt)

        assert self.node.out.get(context) is False


class TestValueAboveBelow:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.mock = MockNumberNode()
        self.node = ValueStaysAboveBelowNode()
        self.node.SAMPLES = 2
        self.node.timespan.set(timedelta(days=1))
        self.node.threshold.set(50)
        self.node.inVal.connect(self.mock.out)

    @pytest.fixture()
    def dt(self):
        return fake.date_time()

    @pytest.mark.parametrize(
        "direction, values, expected_output",
        [
            ("above", [51, 100], True),
            ("above", [49, 100], False),
            ("above", [100, 49], False),
            ("above", [0, 0], False),
            ("below", [49, 49], True),
            ("below", [49, 100], False),
            ("below", [100, 49], False),
            ("below", [100, 100], False),
        ],
    )
    def test_node(self, dt, direction, values, expected_output):
        self.node.direction.set(direction)
        self.mock.set_value(values[0], dt - timedelta(days=1))
        self.mock.set_value(values[1], dt - timedelta(days=0))

        context = ExecutionContext(None, set(), dt)

        assert self.node.out.get(context) is expected_output


class TestValueRisenFallen:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.mock = MockNumberNode()
        self.node = ValueRisenFallenNode()
        self.node.SAMPLES = 3
        self.node.timespan.set(timedelta(days=2))
        self.node.inValue.connect(self.mock.out)

    @pytest.fixture()
    def dt(self):
        return fake.date_time()

    @pytest.mark.parametrize(
        "direction, threshold, values, expected_output",
        [
            ("risen", 10, [10, 20, 30], True),
            ("risen", 10, [10, 15, 20], True),
            ("risen", 10, [10, 10, 100], True),
            ("risen", 10, [10, 15, 19], False),
            ("risen", 10, [30, 20, 10], False),
            ("risen", 10, [0, 0, 0], False),
            ("fallen", 10, [30, 20, 10], True),
            ("fallen", 10, [20, 15, 10], True),
            ("fallen", 10, [100, 10, 10], True),
            ("fallen", 10, [19, 15, 10], False),
            ("fallen", 10, [10, 20, 30], False),
            ("fallen", 10, [0, 0, 0], False),
        ],
    )
    def test_node(self, dt, direction, threshold, values, expected_output):
        self.node.direction.set(direction)
        self.node.threshold.set(threshold)
        self.mock.set_value(values[0], dt - timedelta(days=2))
        self.mock.set_value(values[1], dt - timedelta(days=1))
        self.mock.set_value(values[2], dt - timedelta(days=0))

        context = ExecutionContext(None, set(), dt)

        assert self.node.out.get(context) is expected_output
