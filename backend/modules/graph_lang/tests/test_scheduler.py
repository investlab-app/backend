from decimal import Decimal
from collections import Counter
import pytest
from unittest.mock import patch
from modules.graph_lang.framework.scheduler import Scheduler, SchedulerGraph
from modules.graph_lang.framework.nodes import (
    CheckEveryNode,
    BoughtSoldNode,
    PriceTriggerNode,
)
from datetime import timedelta, datetime


class MockRunner:
    def __init__(self) -> None:
        self.ran_graphs = Counter()

    def run(self, id: str) -> None:
        self.ran_graphs.update([id])

    def get_ran_graphs_counter(self) -> Counter:
        return self.ran_graphs


class MockSchedulerProvider:
    def __init__(self) -> None:
        self.graphs = {}

    def get_graph(self, id: str) -> SchedulerGraph:
        return self.graphs[id]

    def set_graph(self, graph: SchedulerGraph) -> None:
        self.graphs[graph.id] = graph

    def remove_graph(self, id: str) -> None:
        self.graphs.pop(id)


class MockDateTime:
    def __init__(self):
        self._now = datetime.now()

    def now(self):
        return self._now

    def skip_time(self, td: timedelta):
        self._now += td


class TestSchedulerBase:
    @pytest.fixture(autouse=True)
    def setup(self, datetime_mock):
        self.datetime = datetime_mock
        self.runner = MockRunner()
        self.provider = MockSchedulerProvider()
        self.scheduler = Scheduler(
            self.runner, self.provider, max_sleep_timespan=timedelta(days=30)
        )

    @pytest.fixture()
    def datetime_mock(self):
        with patch(
            "modules.graph_lang.framework.scheduler.datetime", new_callable=MockDateTime
        ) as mock:
            yield mock

    def add_timer_node(self, id, td, investor_id="1"):
        node = CheckEveryNode()
        node.timespan.set(td)
        graph = SchedulerGraph(id=id, investor_id=investor_id, trigger=node)
        self.provider.set_graph(graph)
        self.scheduler.add_graph(id)

    def add_price_trigger_node(
        self,
        graph_id: str,
        ticker: str,
        price_threshold: Decimal,
        price_over: bool,
        investor_id="1",
    ):
        node = PriceTriggerNode()
        node.ticker.set(ticker)
        node.price.set(price_threshold)
        node.direction.set("over" if price_over else "under")
        graph = SchedulerGraph(id=graph_id, investor_id=investor_id, trigger=node)
        self.provider.set_graph(graph)
        self.scheduler.add_graph(graph_id)

    def add_transaction_trigger_node(
        self, graph_id: str, ticker: str, is_buy: bool, investor_id="1"
    ):
        node = BoughtSoldNode()
        node.ticker.set(ticker)
        node.action.set("bought" if is_buy else "sold")
        graph = SchedulerGraph(id=graph_id, investor_id=investor_id, trigger=node)
        self.provider.set_graph(graph)
        self.scheduler.add_graph(graph_id)

    def skip_days(self, days):
        self.datetime.skip_time(timedelta(days=days))
        self.scheduler.step()

    def skip_hours(self, hours):
        self.datetime.skip_time(timedelta(hours=hours))
        self.scheduler.step()

    def assert_graphs_ran(self, graphs):
        assert self.runner.get_ran_graphs_counter() == Counter(graphs)


class TestScheduler(TestSchedulerBase):
    def test_no_graph__no_graph_is_ran(self):
        self.scheduler.step()

        self.assert_graphs_ran([])

    def test_remove_graph__invalid_id_passed__gets_ignored(self):
        self.scheduler.remove_graph("test")

    def test_add_graph__graph_does_not_exist__gets_ignored(self):
        self.scheduler.add_graph("test")

    def test_update_graph__graph_does_not_exist__gets_ignored(self):
        self.scheduler.add_graph("test")


class TestMultipleTimersScheduler(TestSchedulerBase):
    @pytest.fixture(autouse=True)
    def setup_multiple_timer(self):
        self.add_timer_node(id="1", td=timedelta(days=3))
        self.add_timer_node(id="2", td=timedelta(days=4))
        self.add_timer_node(id="3", td=timedelta(days=2))

    def test_multiple_timer_graphs__max_sleep_is_earliest_timedelta(self):
        max_sleep = self.scheduler.get_max_idle_datetime()
        expected = self.datetime.now() + timedelta(days=2)

        assert max_sleep == expected

    def test_multiple_timer_graphs__skip_time__some_graphs_are_ran(self):
        self.skip_days(3)

        self.assert_graphs_ran(["1", "3"])


class TestSingleTimerScheduler(TestSchedulerBase):
    @pytest.fixture(autouse=True)
    def setup_single_timer(self):
        self.add_timer_node(id="1", td=timedelta(days=1))

    def test_single_timer_graph__no_step__no_graph_ran(self):
        self.scheduler.step()
        self.assert_graphs_ran([])

    def test_single_timer_graph__max_sleep_equals_timedelta(self):
        max_sleep = self.scheduler.get_max_idle_datetime()
        assert max_sleep == self.datetime.now() + timedelta(days=1)

    def test_default_max_is_biggest_sleep__max_sleep_is_default(self):
        self.scheduler.max_sleep_timespan = timedelta(days=1)

        max_sleep = self.scheduler.get_max_idle_datetime()
        assert max_sleep == (self.datetime.now() + timedelta(days=1))

    def test_single_timer_graph__after_specified_time__is_ran(self):
        self.skip_days(1)

        self.assert_graphs_ran(["1"])

    def test_single_timer_graph__graph_is_ran__multiple_times(self):
        for _ in range(4):
            self.skip_hours(12)

        self.assert_graphs_ran(["1", "1"])

    def test__graph_is_deleted__no_graph_is_ran(self):
        self.scheduler.remove_graph("1")
        self.skip_days(1)

        self.assert_graphs_ran([])

    def test__graph_is_updated__timer_gets_reset(self):
        self.skip_hours(12)
        self.add_timer_node("1", timedelta(days=1, hours=1))
        self.scheduler.update_graph("1")

        self.skip_days(1)
        self.assert_graphs_ran([])
        self.skip_hours(1)
        self.assert_graphs_ran(["1"])


class TestPriceTriggerScheduler(TestSchedulerBase):
    def test__price_trigger__not_triggered__no_ran_graphs(self):
        self.add_price_trigger_node("1", "aapl", 20, price_over=True)

        self.scheduler.price_changed({"aapl": 19})

        self.assert_graphs_ran([])

    def test__price_trigger__triggered__graph_ran(self):
        self.add_price_trigger_node("1", "aapl", 20, price_over=True)

        self.scheduler.price_changed({"aapl": 21})

        self.assert_graphs_ran(["1"])

    def test__two_price_triggers__one_triggered__single_graph_ran(self):
        self.add_price_trigger_node("1", "aapl", 20, price_over=True)
        self.add_price_trigger_node("2", "aapl", 20, price_over=False)

        self.scheduler.price_changed({"aapl": 19})

        self.assert_graphs_ran(["2"])

    def test__two_price_triggers_different_names__both_triggered__both_graphs_ran(self):
        self.add_price_trigger_node("1", "aapl", 20, price_over=True)
        self.add_price_trigger_node("2", "gogl", 10, price_over=False)

        self.scheduler.price_changed({"aapl": 21, "gogl": 9})

        self.assert_graphs_ran(["1", "2"])

    def test__price_trigger__is_case_insensitive(self):
        self.add_price_trigger_node("1", "AaPl", 20, price_over=True)

        self.scheduler.price_changed({"aApL": 21})

        self.assert_graphs_ran(['1'])


class TestTransactionTriggerScheduler(TestSchedulerBase):
    def test__transaction_trigger__triggered_different_investor__no_ran_graphs(self):
        self.add_transaction_trigger_node("1", "aapl", is_buy=True, investor_id="1")
        self.add_transaction_trigger_node("2", "aapl", is_buy=False, investor_id="1")

        self.scheduler.buy_executed(investor_id="2", ticker="aapl", amount=10)
        self.scheduler.sell_executed(investor_id="2", ticker="aapl", amount=10)

        self.assert_graphs_ran([])

    def test__transaction_trigger__transaction_executed__graphs_ran(self):
        self.add_transaction_trigger_node("1", "aapl", is_buy=True, investor_id="1")
        self.add_transaction_trigger_node("2", "aapl", is_buy=False, investor_id="1")

        self.scheduler.buy_executed(investor_id="1", ticker="aapl", amount=10)
        self.scheduler.sell_executed(investor_id="1", ticker="aapl", amount=10)

        self.assert_graphs_ran(["1", "2"])

    def test__transaction_trigger__ticker_does_not_match__no_graphs_ran(self):
        self.add_transaction_trigger_node("1", "aapl", is_buy=True, investor_id="1")
        self.add_transaction_trigger_node("2", "aapl", is_buy=False, investor_id="1")

        self.scheduler.buy_executed(investor_id="1", ticker="gogl", amount=10)
        self.scheduler.sell_executed(investor_id="1", ticker="gogl", amount=10)

        self.assert_graphs_ran([])

    def test_transaction_trigger__ticker_is_case_insensitive(self):
        self.add_transaction_trigger_node("1", "AaPl", is_buy=True, investor_id="1")
        self.add_transaction_trigger_node("2", "AaPl", is_buy=False, investor_id="1")

        self.scheduler.buy_executed(investor_id="1", ticker="aApL", amount=10)
        self.scheduler.sell_executed(investor_id="1", ticker="aApL", amount=10)

        self.assert_graphs_ran(["1", "2"])


class TestSchedulerIntegration(TestSchedulerBase):
    def test_integration__all_graphs_ran(self):
        self.add_timer_node("1", td=timedelta(days=1), investor_id="1")
        self.add_price_trigger_node(
            "2", "aapl", price_threshold=20, price_over=True, investor_id="1"
        )
        self.add_transaction_trigger_node("3", "aapl", is_buy=True, investor_id="1")

        self.skip_days(1)
        self.scheduler.price_changed({"aapl": 30})
        self.scheduler.buy_executed("1", "aapl", 30)

        self.assert_graphs_ran(['1','2','3'])


# TODO set price graph inactive after running
# TODO change provider to db access and builder
# TODO move runner to a different thread