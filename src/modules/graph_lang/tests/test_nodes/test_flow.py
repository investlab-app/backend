import pytest
from faker import Faker

from modules.graph_lang.framework.nodes import (
    FlowIfNode,
)
from modules.graph_lang.framework.nodes.node import ExecutionContext
from modules.graph_lang.tests.conftest_nodes import (
    VoidSensorNode,
)

fake = Faker()


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

    context = ExecutionContext(None, set(), fake.date_time())

    assert node.out.get(context) is None
    assert then_node.executed == then_executed
    assert else_node.executed == else_executed
