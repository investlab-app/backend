from faker import Faker

from modules.graph_lang.framework.nodes.node import ExecutionContext
from modules.graph_lang.tests.conftest_nodes import (
    NumberBasedOnTimeNode,
    PassNumberNode,
)

fake = Faker()


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

    context = ExecutionContext(None, set(), dt_2)

    assert node_1.out.get(context) == 2
