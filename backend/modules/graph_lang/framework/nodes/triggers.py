from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import Node, ExecutionContext


class CheckEveryNode(Node):
    TYPE_NAME = 'checkEvery'
    TRIGGER = True

    timespan = edges.TimespanType(direction=edges.INPUT)

    in_ = edges.VoidType(direction=edges.INPUT, source="in")

    def execute(self, context :ExecutionContext):
        self.in_(context)
