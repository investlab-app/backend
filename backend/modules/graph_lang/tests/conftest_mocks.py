from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from modules.graph_lang.framework.parser import GraphData, NodeData, EdgeData


class MockParser:
    def parse(self, json: dict) -> Optional[Any]:
        self.called_with = json
        return self.data

    def set_data(self, data: Any):
        self.data = data

    def get_call_args(self):
        return self.called_with


class MockValidator:
    def __init__(self):
        self.errors = []

    def validate(self, data):
        self.called_with = data
        return self.errors

    def set_errors(self, errors: list):
        self.errors = errors

    def get_call_args(self):
        return self.called_with


@dataclass
class MockValidatorError:
    id: str
    msg: str = field(default="error", init=False)

class MockScheduler:
    def __init__(self):
        self.events = []
        self.max_idle_datetime = datetime.now()

    def add_graph(self, id: str):
        self.events += [f"add graph {id}"]

    def remove_graph(self, id: str):
        self.events += [f"remove graph {id}"]

    def update_graph(self, id: str):
        self.events += [f"update graph {id}"]

    def price_changed(self, prices: dict[str, Decimal]):
        pass

    def transaction_executed(self, investor_id: str, ticker: str, amount: Decimal):
        pass

    def step(self):
        self.events.append("step")

    def get_max_idle_datetime(self) -> datetime:
        return self.max_idle_datetime

    def get_all_events(self):
        return self.events

    def set_max_idle_datetime(self, datetime):
        self.max_idle_datetime = datetime

empty_graph_data = GraphData()
