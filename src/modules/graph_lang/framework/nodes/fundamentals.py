from datetime import timedelta

from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import ExecutionContext, Node
from modules.investors.models import Asset, Investor


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
    TYPE_NAME = "moneyAvailable"

    out = edges.NumberType(direction=edges.OUTPUT)

    def _execute(self, context):
        investor = Investor.objects.get(id=context.investor_id)
        output = investor.balance - investor.blocked_funds
        self.out.set(output)

        context.log(self.id, "Money available", {"out": output})


class NumberOfAssetsNode(Node):
    TYPE_NAME = "numberOfAssets"

    ticker = edges.InstrumentType(direction=edges.INPUT)

    out = edges.NumberType(direction=edges.OUTPUT)

    def _execute(self, context):
        ticker = self._get(self.ticker)
        try:
            asset = Asset.objects.get(
                investor__id=context.investor_id, ticker__ticker__iexact=ticker
            )
            volume = asset.volume
        except Exception:
            volume = 0

        self.out.set(volume)

        context.log(self.id, "Number of assets", {"ticker": ticker, "out": volume})


class ValueOfAssetsNode(Node):
    TYPE_NAME = "valueOfAssets"

    ticker = edges.InstrumentType(direction=edges.INPUT)

    out = edges.NumberType(direction=edges.OUTPUT)

    def _execute(self, context):
        ticker = self._get(self.ticker)
        price = context.price_provider.get_price(ticker, context.time_at)

        try:
            asset = Asset.objects.get(
                investor__id=context.investor_id, ticker__ticker=ticker
            )
            output = asset.volume * price
        except Exception:
            output = 0

        self.out.set(output)

        context.log(self.id, "Number of assets", {"ticker": ticker, "out": output})

    def _get_needed_prices(self):
        return {self.ticker(None): timedelta()}


class RollingAverageNode(Node):
    TYPE_NAME = "indicator"
    SAMPLES = 100

    ticker = edges.InstrumentType(direction=edges.INPUT)
    timespan = edges.TimespanType(direction=edges.INPUT)
    indicator = edges.EnumType(direction=edges.INPUT, allowed_values=["rolling_avg"])

    out = edges.NumberType(direction=edges.OUTPUT)

    def _execute(self, context):
        ticker = self._get(self.ticker)
        timespan = self._get(self.timespan)
        time_at = context.time_at
        time_step = timespan / (self.SAMPLES - 1)

        total_price = 0
        for i in range(self.SAMPLES):
            time = time_at - time_step * i
            price = context.price_provider.get_price(ticker, time)
            total_price += price

        output = total_price / self.SAMPLES

        self.out.set(output)
        context.log(
            self.id,
            "Rolling average",
            {"ticker": ticker, "timespan": timespan, "output": output},
        )

    def _get_needed_prices(self):
        return {self.ticker(None): self.timespan(None)}


class PriceChangeOfNode(Node):
    TYPE_NAME = "priceChange"

    ticker = edges.InstrumentType(direction=edges.INPUT)
    timespan = edges.TimespanType(direction=edges.INPUT)

    out = edges.NumberType(direction=edges.OUTPUT)

    def _execute(self, context):
        ticker = self._get(self.ticker)
        timespan = self._get(self.timespan)
        time_at = context.time_at

        initial_price = context.price_provider.get_price(ticker, time_at - timespan)
        last_price = context.price_provider.get_price(ticker, time_at)

        output = last_price - initial_price

        self.out.set(output)
        context.log(
            self.id,
            "Price change",
            {"ticker": ticker, "timespan": timespan, "output": output},
        )

    def _get_needed_prices(self):
        return {self.ticker(None): self.timespan(None)}
