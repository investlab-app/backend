import pytest
from faker import Faker

from modules.graph_lang.framework.nodes import (
    AndNode,
    NotNode,
    OrNode,
)
from modules.graph_lang.framework.nodes.node import ExecutionContext

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

    context = ExecutionContext(None, set(), fake.date_time())

    assert node.out.get(context) == expected


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

    context = ExecutionContext(None, set(), fake.date_time())

    assert node.out.get(context) == expected


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

    context = ExecutionContext(None, set(), fake.date_time())

    assert node.out.get(context) == expected
