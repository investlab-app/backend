from decimal import Decimal

from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import ExecutionContext, Node

# ruff: noqa: N815


class IsGreaterLesserNode(Node):
    TYPE_NAME = "isGreaterLesser"

    inValue = edges.NumberType(direction=edges.INPUT)
    inX = edges.NumberType(direction=edges.INPUT)
    direction = edges.EnumType(
        direction=edges.INPUT, allowed_values=["greater", "less"]
    )

    out = edges.BoolType(direction=edges.OUTPUT)

    def _execute(self, context: ExecutionContext):
        direction = self._get(self.direction)
        value = self._get(self.inValue)
        x = self._get(self.inX)

        output = value < x if direction == "less" else value > x

        self.out.set(output)

        context.log(self.id, direction, {"inVal": value, "x": x, "output": output})


# TODO check if samples is > 1
class ValueStaysTheSameNode(Node):
    TYPE_NAME = "staysTheSame"
    SAMPLES = 25

    inVal = edges.NumberType(direction=edges.INPUT, source="in")
    timespan = edges.TimespanType(direction=edges.INPUT)
    tolerance = edges.NumberType(direction=edges.INPUT, source="inX")

    out = edges.BoolType(direction=edges.OUTPUT)

    def _execute(self, context):
        timespan = self._get(self.timespan)
        tolerance = self._get(self.tolerance)

        initial_time = context.time_at - timespan
        time_step = (context.time_at - initial_time) / (self.SAMPLES - 1)
        initial_val = self._get(self.inVal, initial_time)

        stayed_same = True
        for i in range(1, self.SAMPLES):
            val = self._get(self.inVal, time_at=initial_time + i * time_step)
            if abs(val - initial_val) > tolerance:
                stayed_same = False
                break

        self.out.set(stayed_same)
        context.log(
            self.id,
            "Value stays the same",
            fields={
                "timespan": timespan,
                "tolerance": tolerance,
                "output": stayed_same,
            },
        )

    def _get_working_timespan(self):
        return self.timespan(None)


# TODO check if samples is > 1
class ValueStaysAboveBelowNode(Node):
    TYPE_NAME = "staysAboveBelow"
    SAMPLES = 25

    inVal = edges.NumberType(direction=edges.INPUT, source="inValue")
    timespan = edges.TimespanType(direction=edges.INPUT)
    threshold = edges.NumberType(direction=edges.INPUT, source="inX")
    direction = edges.EnumType(direction=edges.INPUT, allowed_values=["above", "below"])

    out = edges.BoolType(direction=edges.OUTPUT)

    def _execute(self, context):
        timespan = self._get(self.timespan)
        threshold = self._get(self.threshold)
        direction = self._get(self.direction)

        initial_time = context.time_at - timespan
        time_step = timespan / (self.SAMPLES - 1)

        output = True
        for i in range(self.SAMPLES):
            val = self._get(self.inVal, time_at=initial_time + i * time_step)
            if direction == "above" and val < threshold:
                output = False
                break
            if direction == "below" and val > threshold:
                output = False
                break

        self.out.set(output)
        context.log(
            self.id,
            "Value stays below",
            fields={
                "timespan": timespan,
                "threshold": threshold,
                "output": output,
            },
        )

    def _get_working_timespan(self):
        return self.timespan(None)


class ValueRisenFallenNode(Node):
    TYPE_NAME = "hasRisenFallen"
    SAMPLES = 25

    inValue = edges.NumberType(direction=edges.INPUT)
    direction = edges.EnumType(
        direction=edges.INPUT, allowed_values=["risen", "fallen"]
    )
    threshold = edges.NumberType(direction=edges.INPUT, source="inX")
    timespan = edges.TimespanType(direction=edges.INPUT)

    out = edges.BoolType(direction=edges.OUTPUT)

    def _execute(self, context):
        direction = self._get(self.direction)
        threshold = self._get(self.threshold)
        timespan = self._get(self.timespan)
        initial_time = context.time_at - timespan

        time_step = timespan / (self.SAMPLES - 1)
        recorded_values = []

        output = False
        for i in range(self.SAMPLES):
            val = self._get(self.inValue, time_at=initial_time + i * time_step)
            recorded_values.append(val)
            if direction == "risen" and self.has_risen_more_than_threshold(
                recorded_values, threshold
            ):
                output = True
                break
            if direction == "fallen" and self.has_fallen_more_than_threshold(
                recorded_values, threshold
            ):
                output = True
                break

        self.out.set(output)

        context.log(
            self.id,
            "value risen/fallen",
            {
                "direction": direction,
                "threshold": threshold,
                "timespan": timespan,
                "output": output,
            },
        )

    def has_risen_more_than_threshold(self, values: list[Decimal], threshold: Decimal):
        n = len(values)
        for i in range(n):
            for j in range(i + 1, n):
                if values[j] - values[i] >= threshold:
                    return True
        return False

    def has_fallen_more_than_threshold(self, values: list[Decimal], threshold: Decimal):
        n = len(values)
        for i in range(n):
            for j in range(i + 1, n):
                if values[j] - values[i] <= -threshold:
                    return True
        return False

    def _get_working_timespan(self):
        return self.timespan(None)


class OccurredXTimesNode(Node):
    SAMPLES = 50

    times = edges.NumberType(direction=edges.INPUT)
    timespan = edges.TimespanType(direction=edges.INPUT)
    interval = edges.TimespanType(direction=edges.INPUT, source="timespan2")
    inValue = edges.BoolType(direction=edges.INPUT, source="in")

    out = edges.BoolType(direction=edges.OUTPUT)

    def _execute(self, context):
        timespan = self._get(self.timespan)
        interval = self._get(self.interval)
        time_step = timespan / (self.SAMPLES - 1)
        times = self._get(self.times)

        min_time = context.time_at - timespan
        max_time = context.time_at
        occurrences = 0

        current_time = min_time
        output = False
        while current_time <= max_time:
            in_val = self._get(self.inValue, current_time)
            if in_val:
                occurrences += 1
                current_time += interval
            else:
                current_time += time_step

            if occurrences >= times:
                output = True
                break

        self.out.set(output)

        context.log(
            self.id,
            "Occurred X times",
            {"timespan": timespan, "interval": interval, "times": times},
        )

    def _get_working_timespan(self):
        return self.timespan(None)
