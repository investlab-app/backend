from dataclasses import dataclass
from datetime import datetime
from typing import Any
from modules.graph_lang.framework import edges


@dataclass
class IsGreaterLesserNode:
    pass


class Node:
    def __init__(self):
        pass

    def execute(self):
        pass

class NodeOutput:
    node :Node
    name :str

    def get(self):
        result = self.node.execute()
        return result[self.name]


class Connection:
    output :NodeOutput

    def get(self, time_at :datetime):
        return self.output.get()

class NodeData:
    value :Any

    def get(self, time_at :datetime):
        return self.value


    

class AndNode(Node):
    inA = edges.BoolType(direction=edges.INPUT)
    inB = edges.BoolType(direction=edges.INPUT)

    out = edges.BoolType(direction=edges.OUTPUT)

    def execute(self, time_at :datetime):
        a = self.inA.get(time_at)
        b = self.inB.get(time_at)

        return {
            'out': a and b
        }

class OrNode(Node):
    inA = edges.BoolType(direction=edges.INPUT)
    inB = edges.BoolType(direction=edges.INPUT)

    out = edges.BoolType(direction=edges.OUTPUT)

    def execute(self, time_at :datetime):
        a = self.inA.get(time_at)
        b = self.inB.get(time_at)

        self.out.set(a or b)


class NotNode(Node):
    inVal = edges.BoolType(direction=edges.INPUT, source='in')
    out = edges.BoolType(direction=edges.OUTPUT)

    def execute(self, time_at :datetime):
        val = self.inVal.get(time_at)

        self.out.set(val)

class IsGreaterLesser(Node):
    inValue = edges.NumberType(direction=edges.INPUT)
    inX = edges.NumberType(direction=edges.INPUT)
    direction = edges.EnumType(direction=edges.INPUT, allowed_values=['greater', 'lesser'])

    out = edges.BoolType(direction=edges.OUTPUT)

    def execute(self, time_at :datetime):
        direction = self.direction.get(time_at)
        value = self.inValue.get(time_at)
        x = self.inX.get(time_at)

        if direction == 'lesser':
            self.out.set(value < x)
        else:
            self.out.set(value > x)

class PriceOfNode(Node):
    ticker = edges.InstrumentType(direction=edges.INPUT)

    out = edges.NumberType(direction=edges.OUTPUT)

    def execute(self, time_at :datetime):
        raise NotImplementedError()

class FlowIfNode(Node):
    inIf = edges.BoolType(direction=edges.INPUT)
    inThen = edges.VoidType(direction=edges.INPUT)
    inElse = edges.VoidType(direction=edges.INPUT)

    out = edges.VoidType(direction=edges.OUTPUT)

    def execute(self, time_at :datetime):
        inIf = self.inIf.get(time_at)

        if inIf:
            self.inThen.get(time_at)
        else:
            self.inElse.get(time_at)

class BuySellAmountNode(Node):
    action = edges.EnumType(direction=edges.INPUT, allowed_values=['buy', 'sell'])
    amount = edges.NumberType(direction=edges.INPUT)
    ticker = edges.InstrumentType(direction=edges.INPUT)

    def execute(self, time_at :datetime):
        raise NotImplementedError()

class CheckEvery(Node):
    timespan = edges.TimespanType(direction=edges.INPUT)

    in_ = edges.VoidType(direction=edges.INPUT, source='in')

    def execute(self, time_at :datetime):
        self.in_.get(time_at)