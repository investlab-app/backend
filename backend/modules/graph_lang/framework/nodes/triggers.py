from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import Node


class CheckEveryNode(Node):
    TYPE_NAME = 'checkEvery'
    TRIGGER = True

    timespan = edges.TimespanType(direction=edges.INPUT)

    in_ = edges.VoidType(direction=edges.INPUT, source="in")

    def execute(self):
        self.in_()
