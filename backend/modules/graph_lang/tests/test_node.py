from datetime import datetime, timedelta

import pytest
from faker import Faker

from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes import Node
from modules.graph_lang.framework.price_provider import PrefetchRange

fake = Faker()


class MockPriceProvider:
    def __init__(self):
        self.result = set()

    def lazy_prefetch_single_ticker(self, ticker: str, data_range: PrefetchRange):
        self.result.add((ticker, data_range.min_time, data_range.max_time))

    def get_results(self) -> set:
        return self.result


class NodeA(Node):
    def prefetch_data(self, data_range):
        pass


class TickerNode(Node):
    out = edges.BoolType(direction=edges.OUTPUT)

    def __init__(self, ticker: str):
        super().__init__()
        self._ticker = ticker

    def _get_needed_prices(self):
        return {self._ticker: timedelta(0)}


class PassByNode(Node):
    in_val = edges.BoolType(direction=edges.INPUT)
    out = edges.BoolType(direction=edges.OUTPUT)


class BranchNode(Node):
    in_a = edges.BoolType(direction=edges.INPUT)
    in_b = edges.BoolType(direction=edges.INPUT)
    out = edges.BoolType(direction=edges.OUTPUT)


class TimeAwareNode(Node):
    in_val = edges.BoolType(direction=edges.INPUT)
    out = edges.BoolType(direction=edges.OUTPUT)

    def __init__(self, timespan):
        super().__init__()
        self._timespan = timespan

    def _get_working_timespan(self):
        return self._timespan


class TestNode:
    def date_pair(self):
        d1, d2 = fake.date_time(), fake.date_time()
        if d1 < d2:
            return d1, d2
        else:
            return d2, d1

    def test__single_node_not_time_aware__prefetch_data__does_nothing(self):
        node = NodeA()

        data = node.calculate_needed_historical_prices()

        assert data == {}

    def test__ticker_node__prefetch_data__prefetches_data(self):
        node = TickerNode("AAPL")

        data = node.calculate_needed_historical_prices()

        assert data == {"AAPL": timedelta()}

    def test__time_aware_node__prefetch_data__passes_down_to_children(self):
        time_node = TimeAwareNode(timespan=timedelta(days=1))
        node = TickerNode("AAPL")
        time_node.in_val.connect(node.out)

        data = time_node.calculate_needed_historical_prices()

        assert data == {"AAPL": timedelta(days=1)}

    def test__prefetch_call_gets_automatically_passed_down(self):
        ticker_node = TickerNode("AAPL")
        pass_by_node = PassByNode()
        time_aware_node = TimeAwareNode(timespan=timedelta(days=4))

        pass_by_node.in_val.connect(ticker_node.out)
        time_aware_node.in_val.connect(pass_by_node.out)

        data = time_aware_node.calculate_needed_historical_prices()

        assert data == {"AAPL": timedelta(days=4)}

    def test__integration(self):
        root = TimeAwareNode(timespan=timedelta(days=1))
        pass_by = PassByNode()
        branch = BranchNode()
        ticker_1 = TickerNode("AAPL")
        time_aware = TimeAwareNode(timespan=timedelta(days=2))
        ticker_2 = TickerNode("MSQ")

        root.in_val.connect(pass_by.out)
        pass_by.in_val.connect(branch.out)
        branch.in_a.connect(ticker_1.out)
        branch.in_b.connect(time_aware.out)
        time_aware.in_val.connect(ticker_2.out)

        data = root.calculate_needed_historical_prices()

        assert data == {"AAPL": timedelta(days=1), "MSQ": timedelta(days=3)}
