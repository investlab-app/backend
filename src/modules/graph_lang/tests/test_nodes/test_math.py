from decimal import Decimal

import pytest
from faker import Faker

from modules.graph_lang.framework.nodes import (
    AddNode,
    DivideNode,
    MultiplyNode,
    NumericIfNode,
    SubtractNode,
)
from modules.graph_lang.framework.nodes.node import ExecutionContext

fake = Faker()


@pytest.mark.parametrize(
    "in_a, in_b, expected",
    [
        (2, 3, 5),
        (-1, 2, 1),
        (0, 0, 0),
    ],
)
def test_add_node(in_a, in_b, expected):
    node = AddNode()
    node.inA.set(in_a)
    node.inB.set(in_b)

    context = ExecutionContext(None, set(), fake.date_time())

    assert node.out.get(context) == expected


@pytest.mark.parametrize(
    "in_a, in_b, expected",
    [
        (5, 3, 2),
        (3, 5, -2),
        (0, 0, 0),
    ],
)
def test_subtract_node(in_a, in_b, expected):
    node = SubtractNode()
    node.inA.set(in_a)
    node.inB.set(in_b)

    context = ExecutionContext(None, set(), fake.date_time())

    assert node.out.get(context) == expected


@pytest.mark.parametrize(
    "in_a, in_b, expected",
    [
        (2, 3, 6),
        (-4, 3, -12),
        (0, 7, 0),
    ],
)
def test_multiply_node(in_a, in_b, expected):
    node = MultiplyNode()
    node.inA.set(in_a)
    node.inB.set(in_b)

    context = ExecutionContext(None, set(), fake.date_time())

    assert node.out.get(context) == expected


@pytest.mark.parametrize(
    "in_a, in_b, expected",
    [
        (9, 3, 3),
        (-8, 2, -4),
        (7, 2, 3.5),
    ],
)
def test_divide_node(in_a, in_b, expected):
    node = DivideNode()
    node.inA.set(in_a)
    node.inB.set(in_b)

    context = ExecutionContext(None, set(), fake.date_time())

    assert node.out.get(context) == expected


def test_divide_node__division_by_zero():
    node = DivideNode()
    node.inA.set(1)
    node.inB.set(0)

    context = ExecutionContext(None, set(), fake.date_time())

    with pytest.raises(RuntimeError, match="Dividend can not be 0!"):
        node.out.get(context)


@pytest.mark.parametrize(
    "if_value, expected_output",
    [
        (True, 10),
        (False, 5),
    ],
)
def test_flow_if_node(if_value, expected_output):
    node = NumericIfNode()
    node.inIf.set(if_value)
    node.inThen.set(10)
    node.inElse.set(5)

    context = ExecutionContext(None, set(), fake.date_time())

    assert node.out.get(context) == Decimal(expected_output)
