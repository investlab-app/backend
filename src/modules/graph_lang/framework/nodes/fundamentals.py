from datetime import timedelta

from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import ExecutionContext, Node
from modules.investors.models import Investor, Asset


class PriceOfNode(Node):
    TYPE_NAME = "priceOf"

    ticker = edges.InstrumentType(direction=edges.INPUT)

    out = edges.NumberType(direction=edges.OUTPUT)

    def _execute(self, context: ExecutionContext):
        ticker = self._get(self.ticker)
        price = context.price_provider.get_price(ticker, context.time_at)
        self.out.set(price)

        context.log(
            self.id,
            "Price of",
            {"ticker": ticker, "time_at": context.time_at, "out": price},
        )

    def _get_needed_prices(self) -> dict[str, timedelta]:
        return {self._get(self.ticker): timedelta()}

class MoneyAvailableNode(Node):
    TYPE_NAME = 'moneyAvailable'

    out = edges.NumberType(direction=edges.OUTPUT)

    def _execute(self, context):
        investor = Investor.objects.get(id = context.investor_id)
        output = investor.balance - investor.blocked_funds
        self.out.set(output)

        context.log(
            self.id,
            "Money available",
            {'out': output}
        )

class NumberOfAssetsNode(Node):
    TYPE_NAME = 'numberOfAssets'
    
    ticker = edges.InstrumentType(direction=edges.INPUT)

    out = edges.NumberType(direction=edges.OUTPUT)

    def _execute(self, context):
        ticker = self._get(self.ticker)
        try:
            asset = Asset.objects.get(investor__id = context.investor_id, ticker__ticker__iexact = ticker)
            volume = asset.volume
        except Exception:
            volume = 0

        self.out.set(volume)

        context.log(
            self.id,
            'Number of assets',
            {'ticker': ticker, 'out': volume}
        )

class ValueOfAssetsNode(Node):
    TYPE_NAME = 'valueOfAssets'

    ticker = edges.InstrumentType(direction=edges.INPUT)

    out = edges.NumberType(direction=edges.OUTPUT)
    
    def _execute(self, context):
        ticker = self._get(self.ticker)
        price = context.price_provider.get_price(ticker, context.time_at)

        try:
            asset = Asset.objects.get(investor__id = context.investor_id, ticker__ticker = ticker)
            output = asset.volume * price
        except Exception:
            output = 0

        self.out.set(output)

        context.log(
            self.id,
            'Number of assets',
            {'ticker': ticker, 'out': output}
        )

    def _get_needed_prices(self):
        return {self.ticker(None): timedelta()}