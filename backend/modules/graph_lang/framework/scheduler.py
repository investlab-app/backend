from decimal import Decimal
from modules.graph_lang.framework.nodes import CheckEveryNode, Node
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

    def __init__(self, runner, provider, max_sleep_timespan=timedelta(minutes=1)):
        self.runner = runner
        self.provider = provider
        self.graphs = []
        self.max_sleep_timespan = max_sleep_timespan
        self.last_run_time = {}

    def add_graph(self, id: str):
        try:
            graph: SchedulerGraph = self.provider.get_graph(id)
            self.graphs.append(graph)
            self.last_run_time[id] = datetime.now()
        except Exception:
            logging.error(
                f"Tried to add graph that does not exist to scheduler. Graph id: {id}"
            )

    def remove_graph(self, id: str):
        graph = next((g for g in self.graphs if g.id == id), None)
        if graph:
            self.graphs.remove(graph)
            self.last_run_time.pop(id)
        else:
            logging.error(
                f"Tried to remove graph that does not exist from scheduler. Graph id: {id}"
            )

    def update_graph(self, id: str):
        self.remove_graph(id)
        self.add_graph(id)

    def price_changed(self, prices: dict[str, Decimal]):
        raise NotImplementedError()

    def transaction_executed(self, investor_id: str, ticker: str, amount: Decimal):
        raise NotImplementedError()

    def step(self):
        for graph in self.graphs:
            should_execute_at = self.last_run_time[graph.id] + graph.trigger.timespan(None)
            if datetime.now() >= should_execute_at:
                self.runner.run(graph.id)
                self.last_run_time[graph.id] = datetime.now()

    def get_max_idle_datetime(self) -> datetime:
        min_timespan = self.max_sleep_timespan

        for g in self.graphs:
            if g.trigger.timespan(None) < min_timespan:
                min_timespan = g.trigger.timespan(None)

        return datetime.now() + min_timespan
