from faker import Faker

from modules.graph_lang.framework.nodes import (
    ChangeOverTimeNode,
)
from modules.graph_lang.framework.nodes.node import ExecutionContext
from modules.graph_lang.tests.conftest_nodes import (
    NumberBasedOnTimeNode,
)

fake = Faker()


def test_change_over_time_node():
    node = ChangeOverTimeNode()
    number_node = NumberBasedOnTimeNode()
    dt_1 = fake.date_time()
    dt_2 = fake.date_time_between(start_date=dt_1)
    number_node.set_val(3, dt_1)
    number_node.set_val(10, dt_2)

    node.timespan.set(dt_2 - dt_1)
    node.in_.connect(number_node.out)

    context = ExecutionContext(None, set(), dt_2)

    assert node.out.get(context) == 10 - 3
