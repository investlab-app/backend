import pytest
from datetime import datetime
from modules.graph_lang.framework.nodes.node import Node, ExecutionContext, NodeLog
from modules.graph_lang.framework import edges

class EmptyLogNode(Node):
    def __init__(self, id):
        super().__init__()
        self.id = id

class PassNode(EmptyLogNode):
    in_ = edges.VoidType(direction=edges.INPUT)
    out = edges.VoidType(direction=edges.OUTPUT)

    def _execute(self, context):
        self._get(self.in_)
        self.out.set(None)
        context.log(self.id, 'passNode')

class VoidNode(EmptyLogNode):
    out = edges.VoidType(direction=edges.OUTPUT)

    def _execute(self, context):
        self.out.set(None)
        context.log(self.id, 'voidNode')

class BranchNode(EmptyLogNode):
    out = edges.VoidType(direction=edges.OUTPUT)
    in_1 = edges.VoidType(direction=edges.INPUT)
    in_2 = edges.VoidType(direction=edges.INPUT)

    def _execute(self, context):
        self._get(self.in_1)
        self._get(self.in_2)
        self.out.set(None)
        context.log(self.id, 'branchNode')

class RepeatNode(EmptyLogNode):
    out = edges.VoidType(direction=edges.OUTPUT)
    in_ = edges.VoidType(direction=edges.INPUT)

    def _execute(self, context):
        self._get(self.in_)
        self._get(self.in_)
        self.out.set(None)
        context.log(self.id, 'repeatNode')

class TriggerNode(EmptyLogNode):
    in_ = edges.VoidType(direction=edges.INPUT)

    def _execute(self, context):
        self._get(self.in_)
        context.log(self.id, 'triggerNode')

class TestLog:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.context = ExecutionContext(None, None, datetime.now())

    def get_log_levels_and_ids(self):
        logs = self.context.get_logs()
        return [(l.level, l.id) for l in logs]

    def test__exec_single_node__log_execution_contains_the_node(self):
        node = VoidNode('1')

        node.execute(self.context)

        assert self.get_log_levels_and_ids() == [
            (0, '1'),
        ]

    def test__exec_two_nodes_in_hierarchy(self):
        node_1 = TriggerNode('1')
        node_2 = VoidNode('2')
        node_1.in_.connect(node_2.out)

        node_1.execute(self.context)

        assert self.get_log_levels_and_ids() == [
            (0, '1'),
            (1, '2')
        ]

    def test__exec_two_nodes_neighbors(self):
        node_1 = BranchNode('1')
        node_2 = VoidNode('2')
        node_3 = VoidNode('3')
        node_1.in_1.connect(node_2.out)
        node_1.in_2.connect(node_3.out)

        node_1.execute(self.context)

        assert self.get_log_levels_and_ids() == [
            (0, '1'),
            (1, '2'),
            (1, '3'),
        ]

    def test_1(self):
        node_1 = BranchNode('1')
        node_2 = PassNode('2')
        node_3 = PassNode('3')
        node_4 = VoidNode('4')
        node_1.in_1.connect(node_2.out)
        node_2.in_.connect(node_3.out)
        node_1.in_2.connect(node_4.out)

        node_1.execute(self.context)

        assert self.get_log_levels_and_ids() == [
            (0, '1'),
            (1, '2'),
            (2, '3'),
            (1, '4'),
        ]

    def test_1(self):
        root = BranchNode('0')
        branch_1 = BranchNode('1')
        branch_2 = BranchNode('2')
        node_1 = VoidNode('3')
        node_2 = VoidNode('4')
        node_3 = VoidNode('5')
        node_4 = VoidNode('6')

        root.in_1.connect(branch_1.out)
        root.in_2.connect(branch_2.out)

        branch_1.in_1.connect(node_1.out)
        branch_1.in_2.connect(node_2.out)

        branch_2.in_1.connect(node_3.out)
        branch_2.in_2.connect(node_4.out)

        root.execute(self.context)

        assert self.get_log_levels_and_ids() == [
            (0, '0'),
            (1, '1'),
            (2, '3'),
            (2, '4'),
            (1, '2'),
            (2, '5'),
            (2, '6'),
        ]
