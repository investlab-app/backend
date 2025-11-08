from datetime import timedelta
from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import Node, ExecutionContext
from modules.graph_lang.framework.prices import PriceProvider


class PriceOfNode(Node):
    TYPE_NAME = "priceOf"

    ticker = edges.InstrumentType(direction=edges.INPUT)

    out = edges.NumberType(direction=edges.OUTPUT)

    def execute(self, context: ExecutionContext):
        ticker = self.ticker(context)
        price = context.price_provider.get_price(ticker, context.time_at)
        self.out.set(price)


    def _get_needed_prices(self) -> dict[str, timedelta]:
        return {self.ticker(None): timedelta()}