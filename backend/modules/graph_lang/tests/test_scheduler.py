from decimal import Decimal
import uuid
from uuid import UUID
import faker
from modules.graph_lang.tests.conftest import fake_graph
from collections import Counter
import pytest
from unittest.mock import patch
from modules.investors.tests.conftest import create_fake_investor
from modules.investors.models import Investor
from modules.graph_lang.framework.nodes.node import Node
from modules.graph_lang.framework.scheduler import Scheduler, SchedulerGraph
from modules.graph_lang.framework.nodes import (
    CheckEveryNode,
    BoughtSoldNode,
    PriceTriggerNode,
)
from datetime import timedelta, datetime

pytestmark = pytest.mark.django_db

fake = faker.Faker()

class MockRunner:
    def __init__(self):
        self.ran_graphs = Counter()

    def run(self, id: UUID):
        self.ran_graphs.update([id])

    def get_ran_graphs_counter(self) -> Counter:
        return self.ran_graphs


class MockBuilder:
    def __init__(self):
        self.graphs = {}

    def get_from_db(self, id: UUID) -> Node:
        return self.graphs[id]

    def set_graph(self, id: UUID, graph: Node):
        self.graphs[id] = graph

    def remove_graph(self, id: UUID):
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
        self.builder = MockBuilder()
        self.scheduler = Scheduler(
            self.runner, self.builder, max_sleep_timespan=timedelta(days=30)
        )

    @pytest.fixture()
    def datetime_mock(self):
        with patch(
            "modules.graph_lang.framework.scheduler.datetime", new_callable=MockDateTime
        ) as mock:
            yield mock

    @pytest.fixture()
    def uuid(self) -> UUID:
        return uuid.uuid4()

    @pytest.fixture()
    def uuid_factory(self):
        def _uuids(n) -> UUID:
            return [uuid.uuid4() for _ in range(n)]
        return _uuids

    def create_graph(self, id: UUID, investor_id: UUID):
        try:
            investor = Investor.objects.get(id = investor_id)
        except:
            investor = create_fake_investor(investor_id=investor_id, save=True)
        fake_graph(
            id=id,
            investor=investor,
            save=True,
        )

    def add_timer_node(self, id, td, investor_id=None):
        if not investor_id:
            investor_id = fake.uuid4()
        node = CheckEveryNode()
        node.timespan.set(td)
        self.create_graph(id, investor_id)
        self.builder.set_graph(id=id, graph=node)
        self.scheduler.add_graph(id)

    def add_price_trigger_node(
        self,
        graph_id: str,
        ticker: str,
        price_threshold: Decimal,
        price_over: bool,
        investor_id=None,
    ):
        if investor_id is None:
            investor_id = fake.uuid4()
        node = PriceTriggerNode()
        node.ticker.set(ticker)
        node.price.set(price_threshold)
        node.direction.set("over" if price_over else "under")

        self.create_graph(graph_id, investor_id)
        self.builder.set_graph(graph_id, node)

        self.scheduler.add_graph(graph_id)

    def add_transaction_trigger_node(
        self, graph_id: str, ticker: str, is_buy: bool, investor_id=None
    ):
        node = BoughtSoldNode()
        node.ticker.set(ticker)
        node.action.set("bought" if is_buy else "sold")

        if investor_id is None:
            investor_id = fake.uuid4()

        self.create_graph(graph_id, investor_id)
        self.builder.set_graph(graph_id, node)

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
    def setup_multiple_timer(self, uuid_factory):
        self.uuid_1, self.uuid_2, self.uuid_3 = uuid_factory(3)
        self.add_timer_node(id=self.uuid_1, td=timedelta(days=3))
        self.add_timer_node(id=self.uuid_2, td=timedelta(days=4))
        self.add_timer_node(id=self.uuid_3, td=timedelta(days=2))

    def test_multiple_timer_graphs__max_sleep_is_earliest_timedelta(self):
        max_sleep = self.scheduler.get_max_idle_datetime()
        expected = self.datetime.now() + timedelta(days=2)

        assert max_sleep == expected

    def test_multiple_timer_graphs__skip_time__some_graphs_are_ran(self):
        self.skip_days(3)

        self.assert_graphs_ran([self.uuid_1, self.uuid_3])


class TestSingleTimerScheduler(TestSchedulerBase):
    @pytest.fixture(autouse=True)
    def setup_single_timer(self, uuid):
        self.id = uuid
        self.add_timer_node(id=uuid, td=timedelta(days=1))

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

        self.assert_graphs_ran([self.id])

    def test_single_timer_graph__graph_is_ran__multiple_times(self):
        for _ in range(4):
            self.skip_hours(12)

        self.assert_graphs_ran([self.id, self.id])

    def test__graph_is_deleted__no_graph_is_ran(self):
        self.scheduler.remove_graph(self.id)
        self.skip_days(1)

        self.assert_graphs_ran([])

    def test__graph_is_updated__timer_gets_reset(self):
        self.skip_hours(12)
        self.scheduler.update_graph(self.id)

        self.skip_hours(23)
        self.assert_graphs_ran([])
        self.skip_hours(1)
        self.assert_graphs_ran([self.id])


class TestPriceTriggerScheduler(TestSchedulerBase):
    def test__price_trigger__not_triggered__no_ran_graphs(self, uuid):
        self.add_price_trigger_node(uuid, "aapl", 20, price_over=True)

        self.scheduler.price_changed({"aapl": 19})

        self.assert_graphs_ran([])

    def test__price_trigger__triggered__graph_ran(self, uuid):
        self.add_price_trigger_node(uuid, "aapl", 20, price_over=True)

        self.scheduler.price_changed({"aapl": 21})

        self.assert_graphs_ran([uuid])

    def test__two_price_triggers__one_triggered__single_graph_ran(self, uuid_factory):
        uuid_1, uuid_2 = uuid_factory(2)
        self.add_price_trigger_node(uuid_1, "aapl", 20, price_over=True)
        self.add_price_trigger_node(uuid_2, "aapl", 20, price_over=False)

        self.scheduler.price_changed({"aapl": 19})

        self.assert_graphs_ran([uuid_2])

    def test__two_price_triggers_different_names__both_triggered__both_graphs_ran(self, uuid_factory):
        uuid_1, uuid_2 = uuid_factory(2)
        self.add_price_trigger_node(uuid_1, "aapl", 20, price_over=True)
        self.add_price_trigger_node(uuid_2, "gogl", 10, price_over=False)

        self.scheduler.price_changed({"aapl": 21, "gogl": 9})

        self.assert_graphs_ran([uuid_1, uuid_2])

    def test__price_trigger__is_case_insensitive(self, uuid):
        self.add_price_trigger_node(uuid, "AaPl", 20, price_over=True)

        self.scheduler.price_changed({"aApL": 21})

        self.assert_graphs_ran([uuid])


class TestTransactionTriggerScheduler(TestSchedulerBase):
    def test__transaction_trigger__triggered_different_investor__no_ran_graphs(
        self, uuid_factory
    ):
        graph_1, graph_2, investor_1, investor_2 = uuid_factory(4)
        self.add_transaction_trigger_node(
            graph_1, "aapl", is_buy=True, investor_id=investor_1
        )
        self.add_transaction_trigger_node(
            graph_2, "aapl", is_buy=False, investor_id=investor_1
        )

        self.scheduler.buy_executed(investor_id=investor_2, ticker="aapl", amount=10)
        self.scheduler.sell_executed(investor_id=investor_2, ticker="aapl", amount=10)

        self.assert_graphs_ran([])

    def test__transaction_trigger__transaction_executed__graphs_ran(self, uuid_factory):
        graph_1, graph_2, investor_1 = uuid_factory(3)
        self.add_transaction_trigger_node(
            graph_1, "aapl", is_buy=True, investor_id=investor_1
        )
        self.add_transaction_trigger_node(
            graph_2, "aapl", is_buy=False, investor_id=investor_1
        )

        self.scheduler.buy_executed(investor_id=investor_1, ticker="aapl", amount=10)
        self.scheduler.sell_executed(investor_id=investor_1, ticker="aapl", amount=10)

        self.assert_graphs_ran([graph_1, graph_2])

    def test__transaction_trigger__ticker_does_not_match__no_graphs_ran(
        self, uuid_factory
    ):
        graph_1, graph_2, investor_1 = uuid_factory(3)
        self.add_transaction_trigger_node(
            graph_1, "aapl", is_buy=True, investor_id=investor_1
        )
        self.add_transaction_trigger_node(
            graph_2, "aapl", is_buy=False, investor_id=investor_1
        )

        self.scheduler.buy_executed(investor_id=investor_1, ticker="gogl", amount=10)
        self.scheduler.sell_executed(investor_id=investor_1, ticker="gogl", amount=10)

        self.assert_graphs_ran([])

    def test_transaction_trigger__ticker_is_case_insensitive(self, uuid_factory):
        graph_1, graph_2, investor_1 = uuid_factory(3)
        self.add_transaction_trigger_node(
            graph_1, "AaPl", is_buy=True, investor_id=investor_1
        )
        self.add_transaction_trigger_node(
            graph_2, "AaPl", is_buy=False, investor_id=investor_1
        )

        self.scheduler.buy_executed(investor_id=investor_1, ticker="aApL", amount=10)
        self.scheduler.sell_executed(investor_id=investor_1, ticker="aApL", amount=10)

        self.assert_graphs_ran([graph_1, graph_2])


class TestSchedulerIntegration(TestSchedulerBase):
    def test_integration__all_graphs_ran(self, uuid_factory):
        graph_1, graph_2, graph_3, investor_1 = uuid_factory(4)
        self.add_timer_node(graph_1, td=timedelta(days=1), investor_id=investor_1)
        self.add_price_trigger_node(
            graph_2, "aapl", price_threshold=20, price_over=True, investor_id=investor_1
        )
        self.add_transaction_trigger_node(
            graph_3, "aapl", is_buy=True, investor_id=investor_1
        )

        self.skip_days(1)
        self.scheduler.price_changed({"aapl": 30})
        self.scheduler.buy_executed(investor_1, "aapl", 30)

        self.assert_graphs_ran([graph_1, graph_2, graph_3])


# TODO set price graph inactive after running
# TODO move runner to a different thread
# TODO collect mocks into one place
# TODO move uuid fixtures to core
# TODO update types here and in scheduler
# TODO move if investor= None to create_fake_graph