from datetime import datetime
from decimal import Decimal
from modules.graph_lang.framework.nodes import Node
from modules.graph_lang.framework import edges

class VoidSensorNode(Node):
    out = edges.VoidType(direction=edges.OUTPUT)
    executed = False

    def execute(self):
        self.out.set(None)
        self.executed = True

class NumberBasedOnTimeNode(Node):
    out = edges.NumberType(direction=edges.OUTPUT)
    _values = {}
    
    def execute(self):
        val = self._values[self._time_at]
        self.out.set(val)

    def set_val(self, val, time_at):
        self._values[time_at] = val

class PassNumberNode(Node):
    in_ = edges.NumberType(direction=edges.INPUT)

    out = edges.NumberType(direction=edges.OUTPUT)

    def execute(self):
        self.out.set(self.in_())


class PriceProviderMock(Node):
    _prices = {}

    def get(self, ticker :str, time_at :datetime) -> Decimal:
        return self._prices[(ticker, time_at)]

    def set(self, ticker :str, time_at :datetime, price :Decimal):
        self._prices[(ticker, time_at)] = price