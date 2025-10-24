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
    value :Any

    def get(self):
        self.node.execute()
        return self.value

    def set(self, value):
        self.value = value


class Connection:
    node :Node
    output :NodeOutput

    def __call__(self, time_at = None):
        # Propagate time_at to next node
        raise NotImplementedError()

class NodeData:
    value :Any

    def __call__(self, time_at = None):
        return self.value


    

class AndNode(Node):
    inA = edges.BoolType(direction=edges.INPUT)
    inB = edges.BoolType(direction=edges.INPUT)

    out = edges.BoolType(direction=edges.OUTPUT)

    def execute(self):
        a = self.inA()
        b = self.inB()

        return {
            'out': a and b
        }

class OrNode(Node):
    inA = edges.BoolType(direction=edges.INPUT)
    inB = edges.BoolType(direction=edges.INPUT)

    out = edges.BoolType(direction=edges.OUTPUT)

    def execute(self):
        a = self.inA()
        b = self.inB()

        self.out.set(a or b)


class NotNode(Node):
    inVal = edges.BoolType(direction=edges.INPUT, source='in')
    out = edges.BoolType(direction=edges.OUTPUT)

    def execute(self):
        val = self.inVal()

        self.out.set(not val)

class IsGreaterLesser(Node):
    inValue = edges.NumberType(direction=edges.INPUT)
    inX = edges.NumberType(direction=edges.INPUT)
    direction = edges.EnumType(direction=edges.INPUT, allowed_values=['greater', 'lesser'])

    out = edges.BoolType(direction=edges.OUTPUT)

    def execute(self):
        direction = self.direction()
        value = self.inValue()
        x = self.inX()

        if direction == 'lesser':
            self.out.set(value < x)
        else:
            self.out.set(value > x)

class PriceOfNode(Node):
    ticker = edges.InstrumentType(direction=edges.INPUT)

    out = edges.NumberType(direction=edges.OUTPUT)

    def execute(self):
        # How to access time_at?
        raise NotImplementedError()

class FlowIfNode(Node):
    inIf = edges.BoolType(direction=edges.INPUT)
    inThen = edges.VoidType(direction=edges.INPUT)
    inElse = edges.VoidType(direction=edges.INPUT)

    out = edges.VoidType(direction=edges.OUTPUT)

    def execute(self):
        if self.inIf():
            self.inThen()
        else:
            self.inElse()

class BuySellAmountNode(Node):
    action = edges.EnumType(direction=edges.INPUT, allowed_values=['buy', 'sell'])
    amount = edges.NumberType(direction=edges.INPUT)
    ticker = edges.InstrumentType(direction=edges.INPUT)

    def execute(self):
        raise NotImplementedError()

class CheckEveryNode(Node):
    timespan = edges.TimespanType(direction=edges.INPUT)

    in_ = edges.VoidType(direction=edges.INPUT, source='in')

    def execute(self):
        self.in_()

class ChangeOverTimeNode(Node):
    timespan = edges.TimespanType(direction=edges.INPUT)
    in_ = edges.NumberType(direction=edges.INPUT, source='in')

    out = edges.NumberType(direction=edges.OUTPUT)

    def execute(self):
        timespan = self.timespan()
        
        in_now = self.in_()
        in_before = self.in_(time_at = self.time_at - timespan)

        self.out.set(in_now - in_before)


