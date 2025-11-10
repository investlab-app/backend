from decimal import Decimal
from modules.graph_lang.framework.nodes import (
    CheckEveryNode,
    BoughtSoldNode,
    PriceTriggerNode,
    Node,
)
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class SchedulerGraph:
    id: str
    investor_id: str
    trigger: Node


class Scheduler:
    graphs: list[SchedulerGraph]
    last_run_time: dict[str, datetime]
    max_sleep_timespan: timedelta

    def __init__(self, runner, provider, max_sleep_timespan=timedelta(seconds=1)):
        self.runner = runner
        self.provider = provider
        self.graphs = []
        self.max_sleep_timespan = max_sleep_timespan
        self.last_run_time = {}

    def add_graph(self, id: str):
        try:
            self._try_add_graph(id)
        except Exception:
            logging.error(
                f"Tried to add graph that does not exist to scheduler. Graph id: {id}"
            )

    def _try_add_graph(self, id :str):
        graph: SchedulerGraph = self.provider.get_graph(id)
        self.graphs.append(graph)
        self.last_run_time[id] = datetime.now()

    def remove_graph(self, id: str):
        try:
            self._try_remove_graph(id)
        except Exception:
            logging.error(
                f"Tried to remove graph that does not exist from scheduler. Graph id: {id}"
            )

    def _try_remove_graph(self, id :str):
        graph = next(g for g in self.graphs if g.id == id)
        self.graphs.remove(graph)
        self.last_run_time.pop(id)

    def update_graph(self, id: str):
        self.remove_graph(id)
        self.add_graph(id)

    def price_changed(self, prices: dict[str, Decimal]):
        price_graphs = self._get_graphs_with(PriceTriggerNode)
        prices = {ticker.lower(): price for ticker, price in prices.items()}

        for graph in price_graphs:
            ticker, price, direction = self._get_price_trigger_args(graph.trigger)
            ticker = ticker.lower()

            if not ticker in prices:
                continue

            current_price = prices[ticker]
            if (
                current_price > price
                and direction == "over"
                or current_price < price
                and direction == "under"
            ):
                self._run_graph(graph)

    def _get_price_trigger_args(self, trigger):
        ticker = trigger.ticker(None)
        price = trigger.price(None)
        direction = trigger.direction(None)
        return ticker, price, direction

    def buy_executed(self, investor_id: str, ticker: str, amount: Decimal):
        self._run_transaction_graphs(investor_id, ticker, "bought")

    def sell_executed(self, investor_id: str, ticker: str, amount: Decimal):
        self._run_transaction_graphs(investor_id, ticker, "sold")

    def _run_transaction_graphs(self, investor_id: str, ticker: str, action: str):
        transaction_graphs = self._get_graphs_with(BoughtSoldNode)
        affected_graphs = [
            g
            for g in transaction_graphs
            if g.investor_id == investor_id
            and g.trigger.action(None) == action
            and g.trigger.ticker(None).lower() == ticker.lower()
        ]

        for graph in affected_graphs:
            self._run_graph(graph)

    def step(self):
        timer_graphs = self._get_graphs_with(CheckEveryNode)
        for graph in timer_graphs:
            scheduled_execution = self._get_scheduled_execution(graph)
            if datetime.now() >= scheduled_execution:
                self._run_graph(graph)

    def _get_scheduled_execution(self, graph) -> datetime:
        last_run_time = self.last_run_time[graph.id]
        timespan = graph.trigger.timespan(None)
        return last_run_time + timespan

    def get_max_idle_datetime(self) -> datetime:
        max_sleep_date = datetime.now() + self.max_sleep_timespan
        timer_graphs = self._get_graphs_with(CheckEveryNode)

        for graph in timer_graphs:
            scheduled_execution = self._get_scheduled_execution(graph)
            if max_sleep_date > scheduled_execution:
                max_sleep_date = scheduled_execution

        return max_sleep_date

    def _run_graph(self, graph):
        self.runner.run(graph.id)
        self.last_run_time[graph.id] = datetime.now()

    def _get_graphs_with(self, type):
        return [g for g in self.graphs if isinstance(g.trigger, type)]


# TODO normalize how node inputs are get, is it node._get(input) or node.input(None)
