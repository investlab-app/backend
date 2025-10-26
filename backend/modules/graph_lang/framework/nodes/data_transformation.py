from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import Node

class ChangeOverTimeNode(Node):
    timespan = edges.TimespanType(direction=edges.INPUT)
    in_ = edges.NumberType(direction=edges.INPUT, source='in')

    out = edges.NumberType(direction=edges.OUTPUT)

    def execute(self):
        if self._time_at is None:
            raise RuntimeError("Execution time needs to be set for this node to run")

        timespan = self.timespan()
        
        in_now = self.in_()
        in_before = self.in_(self._time_at - timespan)

        self.out.set(in_now - in_before)