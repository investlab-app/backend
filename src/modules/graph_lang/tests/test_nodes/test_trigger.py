from faker import Faker

from modules.graph_lang.framework.nodes import (
    CheckEveryNode,
)
from modules.graph_lang.framework.nodes.node import ExecutionContext
from modules.graph_lang.tests.conftest_nodes import (
    VoidSensorNode,
)

fake = Faker()


def test_check_every_node():
    node = CheckEveryNode()
    void_sensor_node = VoidSensorNode()
    node.in_.connect(void_sensor_node.out)

    context = ExecutionContext(None, set(), fake.date_time())
    node.execute(context)

    assert void_sensor_node.executed is True
