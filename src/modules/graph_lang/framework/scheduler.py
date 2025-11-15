import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from django.db import transaction

from modules.graph_lang.framework.builder import GraphBuilder
from modules.graph_lang.framework.nodes import (
    BoughtSoldNode,
    CheckEveryNode,
    Node,
    PriceTriggerNode,
)
from modules.graph_lang.framework.runner import Runner
from modules.graph_lang.models import Graph

logger = logging.getLogger(__name__)


@dataclass
class SchedulerGraph:
    id: str
    investor_id: str
    trigger: Node
    active: bool
    repeat: bool


class Scheduler:
    graphs: list[SchedulerGraph]
    last_run_time: dict[str, datetime]
    max_sleep_timespan: timedelta
    _builder: GraphBuilder

    def __init__(
        self, runner=None, builder=None, max_sleep_timespan=timedelta(seconds=1)
    ):
        self.runner = runner or Runner()
        self._builder = builder or GraphBuilder()
        self.graphs = []
        self.max_sleep_timespan = max_sleep_timespan
        self.last_run_time = {}

    def add_graph(self, id_: str):
        try:
            self._try_add_graph(id_)
        except Exception:
            logger.error(
                "Tried to add graph that does not exist to scheduler. Graph id: %s",
                id_,
            )

    def _try_add_graph(self, id_: str):
        graph = Graph.objects.get(id=id_)
        node = self._builder.get_from_db(id_)
        graph = SchedulerGraph(
            id=id_,
            investor_id=graph.investor.id,
            trigger=node,
            active=graph.active,
            repeat=graph.repeat,
        )
        self.graphs.append(graph)
        self.last_run_time[id_] = datetime.now()

    def remove_graph(self, id_: str):
        try:
            self._try_remove_graph(id_)
        except Exception:
            logger.error(
                "Removed a graph that does not exist from scheduler. Graph id: %s",
                id_,
            )

    def _try_remove_graph(self, id_: str):
        graph = next(g for g in self.graphs if g.id == id_)
        self.graphs.remove(graph)
        self.last_run_time.pop(id_)

    def update_graph(self, id_: str):
        self.remove_graph(id_)
        self.add_graph(id_)

    def price_changed(self, prices: dict[str, Decimal]):
        price_graphs = self._get_graphs_with(PriceTriggerNode)
        prices = {ticker.lower(): price for ticker, price in prices.items()}

        for graph in price_graphs:
            ticker, price, direction = self._get_price_trigger_args(graph.trigger)
            ticker = ticker.lower()

            if ticker not in prices:
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

    def _run_graph(self, graph: SchedulerGraph):
        if not graph.active:
            return
        if graph.repeat is False:
            self._deactivate_graph(graph)

        self.runner.run(graph.id)
        self.last_run_time[graph.id] = datetime.now()

    def _deactivate_graph(self, graph: SchedulerGraph):
        graph.active = False
        try:
            with transaction.atomic():
                graph_db = Graph.objects.get(id=graph.id)
                graph_db.active = False
                graph_db.save()
        except Exception:
            pass

    def _get_graphs_with(self, type_):
        return [g for g in self.graphs if isinstance(g.trigger, type_)]


# TODO normalize how node inputs are get, is it node._get(input) or node.input(None)
# TODO Make member variables private
