from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from modules.graph_lang.framework.nodes.node import Node
from modules.graph_lang.framework.parser import EdgeData, GraphData, NodeData


class MockParser:
    def parse(self, json: dict) -> Any | None:
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

    def add_graph(self, id_: str):
        self.events += [f"add graph {id_}"]

    def remove_graph(self, id_: str):
        self.events += [f"remove graph {id_}"]

    def update_graph(self, id_: str):
        self.events += [f"update graph {id_}"]

    def price_changed(self, prices: dict[str, Decimal]):
        print(prices)
        self.events += [("prices changed", prices)]

    def buy_executed(self, investor_id: str, ticker: str, amount: Decimal):
        self.events += [f"buy {investor_id} {ticker} {amount}"]

    def sell_executed(self, investor_id: str, ticker: str, amount: Decimal):
        self.events += [f"sell {investor_id} {ticker} {amount}"]

    def step(self):
        self.events.append("step")

    def get_max_idle_datetime(self) -> datetime:
        return self.max_idle_datetime

    def get_all_events(self):
        return self.events

    def set_max_idle_datetime(self, datetime):
        self.max_idle_datetime = datetime


class MockFactory:
    def __init__(self):
        self.types = {}

    def name_to_type(self, name: str) -> type[Node] | None:
        return self.types.get(name, None)

    def register_type(self, name: str, type_: type):
        self.types[name] = type_
