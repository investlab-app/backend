from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import Node, ExecutionContext, NodeLog


class ChangeOverTimeNode(Node):
    TYPE_NAME = "changeOverTime"

    timespan = edges.TimespanType(direction=edges.INPUT)
    in_ = edges.NumberType(direction=edges.INPUT, source="in")

    out = edges.NumberType(direction=edges.OUTPUT)

    def _execute(self, context: ExecutionContext):
        time_at = context.time_at
        timespan = self._get(self.timespan)

        in_now = self._get(self.in_)
        in_before = self._get(self.in_, time_at - timespan)
        output = in_now - in_before

        self.out.set(output)

        context.log(
            self.id,
            "ChangeOverTime",
            {"in_now": in_now, "in_before": in_before, "out": output},
        )

    def _get_working_timespan(self):
        return self._get(self.timespan)
