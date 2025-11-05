import pytest
from modules.graph_lang.framework.price_provider import PrefetchRange
from modules.graph_lang.framework.nodes import Node
from modules.graph_lang.framework import edges
from datetime import timedelta
from faker import Faker


fake = Faker()

class MockPriceProvider:
    def __init__(self):
        self.result = set()

    def lazy_prefetch_single_ticker(self, ticker :str, data_range :PrefetchRange):
        self.result.add((ticker, data_range.min_time, data_range.max_time))

    def get_results(self) -> set:
        return self.result

class NodeA(Node):
    def prefetch_data(self, data_range):
        pass

class TickerNode(Node):
    out = edges.BoolType(direction=edges.OUTPUT)

    def __init__(self, price_provider, ticker :str):
        super().__init__()
        self._price_provider = price_provider
        self._ticker = ticker

    def _prefetch_data(self, data_range):
        self._price_provider.lazy_prefetch_single_ticker(self._ticker, data_range)

class PassByNode(Node):
    inVal = edges.BoolType(direction=edges.INPUT)
    out = edges.BoolType(direction=edges.OUTPUT)

class BranchNode(Node):
    inA = edges.BoolType(direction=edges.INPUT)
    inB = edges.BoolType(direction=edges.INPUT)
    out = edges.BoolType(direction=edges.OUTPUT)

class TimeAwareNode(Node):
    inVal = edges.BoolType(direction=edges.INPUT)

    def __init__(self, timespan):
        super().__init__()
        self._timespan = timespan

    def _get_new_time_range(self, data_range):
        return PrefetchRange(
            data_range.min_time - self._timespan,
            data_range.max_time
        )

class TestNode:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.price_provider = MockPriceProvider()

    def date_pair(self):
        d1, d2 = fake.date_time(), fake.date_time()
        if d1 < d2:
            return d1, d2
        else:
            return d2, d1

    def test__single_node_not_time_aware__prefetch_data__does_nothing(self):
        prefetch_range = PrefetchRange(*self.date_pair())
        node = NodeA()

        node.prefetch_data(prefetch_range)

    def test__ticker_node__prefetch_data__prefetches_data(self):
        date_1, date_2 = self.date_pair()
        node = TickerNode(self.price_provider, 'AAPL')

        node.prefetch_data(PrefetchRange(date_1, date_2))

        assert self.price_provider.get_results() == {
            ('AAPL', date_1, date_2)
        }

    def test__time_aware_node__prefetch_data__passes_down_to_children(self):
        time_node = TimeAwareNode(timespan=timedelta(days=1))
        node = TickerNode(self.price_provider, 'AAPL')
        time_node.inVal.connect(node.out)

        date_1, date_2 = self.date_pair()
        time_node.prefetch_data(PrefetchRange(date_1, date_2))

        assert self.price_provider.get_results() == {
            ('AAPL', date_1 - timedelta(days=1), date_2)
        }

    def test__prefetch_call_gets_automatically_passed_down(self):
        ticker_node = TickerNode(self.price_provider, 'AAPL')
        pass_by_node = PassByNode()
        time_aware_node = TimeAwareNode(timespan=timedelta(days=4))

        pass_by_node.inVal.connect(ticker_node.out)
        time_aware_node.inVal.connect(pass_by_node.out)

        date_1, date_2 = self.date_pair()
        time_aware_node.prefetch_data(PrefetchRange(date_1, date_2))

        assert self.price_provider.get_results() == {
            ('AAPL', date_1 - timedelta(days=4), date_2)
        }

    def integration_test(self):
        # nodes = TimeAwareNode(
        #     timespan=timedelta(days=1),
        #     inVal = PassByNode(
        #         inVal = BranchNode(
        #             inA = TickerNode(self.price_provider, 'AAPL'),
        #             inB = TimeAwareNode(
        #                 timespan=timedelta(days=1),
        #                 inVal = TickerNode(self.price_provider, 'MSQ')
        #             )
        #         )
        #     ) 
        # )

        root = TimeAwareNode(timespan=timedelta(days=1))
        pass_by = PassByNode()
        branch = BranchNode()
        ticker_1 = TickerNode(self.price_provider, 'AAPL')
        time_aware = TimeAwareNode(timespan=timedelta(days=2))
        ticker_2 = TickerNode(self.price_provider, 'MSQ')

        root.inVal.connect(pass_by.out)
        pass_by.inVal.connect(branch.out)
        branch.inA.connect(ticker_1)
        branch.inB.connect(time_aware)
        time_aware.inVal.connect(ticker_2)

        date_1, date_2 = self.date_pair()
        root.prefetch_data(PrefetchRange(date_1, date_2))

        assert self.price_provider.get_results() == {
            ('AAPL', date_1 - timedelta(days=1), date_2),
            ('MSQ', date_1 - timedelta(days=3), date_2)
        }

