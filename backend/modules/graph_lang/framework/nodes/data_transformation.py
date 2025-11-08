from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import Node, ExecutionContext


class ChangeOverTimeNode(Node):
    TYPE_NAME = "changeOverTime"

    timespan = edges.TimespanType(direction=edges.INPUT)
    in_ = edges.NumberType(direction=edges.INPUT, source="in")

    out = edges.NumberType(direction=edges.OUTPUT)

    def execute(self, context: ExecutionContext):
        time = context.time_at

        in_now = self.in_(context)
        context.time_at -= self.timespan(context)
        in_before = self.in_(context)

        context.time_at = time

        self.out.set(in_now - in_before)

    def _get_working_timespan(self):
        return self.timespan(None)
