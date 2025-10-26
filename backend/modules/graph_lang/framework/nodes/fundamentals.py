from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import Node
from modules.graph_lang.framework.prices import PriceProvider


class PriceOfNode(Node):
    ticker = edges.InstrumentType(direction=edges.INPUT)

    out = edges.NumberType(direction=edges.OUTPUT)

    price_provider: PriceProvider

    def __init__(self, price_provider):
        super().__init__()
        self.price_provider = price_provider

    def execute(self):
        if self._time_at is None:
            raise RuntimeError("Execution time needs to be set for this node to run")

        ticker = self.ticker()
        price = self.price_provider.get(ticker, self._time_at)
        self.out.set(price)
