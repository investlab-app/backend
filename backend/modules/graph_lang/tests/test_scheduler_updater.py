import json
from unittest.mock import patch
import pytest
import faker
import asyncio
from config.clients import redis_client
from modules.graph_lang.tests.conftest import fake_graph
from datetime import datetime, timedelta
from modules.graph_lang.framework.scheduler_updater import SchedulerUpdater
from modules.graph_lang.tests.conftest_mocks import MockScheduler
from modules.transactions.tests.conftest import create_fake_transaction
from modules.investors.tests.conftest import create_fake_investor
from modules.instruments.tests.conftest import create_fake_instrument
from modules.prices.constants import PRICES_CHANNEL_LAYER
from modules.prices.tests.conftest import get_fake_ohlc

from channels.layers import get_channel_layer

fake = faker.Faker()
pytestmark = pytest.mark.django_db


class TestSchedulerUpdater:
    @pytest.fixture(autouse=True)
    def setup(self, datetime_mock, sleep_mock):
        self.scheduler = MockScheduler()
        self.updater = SchedulerUpdater(self.scheduler)
        self.datetime = datetime_mock
        self.sleep = sleep_mock

    @pytest.fixture(autouse=True)
    def sleep_mock(self):
        with patch("modules.graph_lang.framework.scheduler_updater.sleep") as mock:
            yield mock

    @pytest.fixture(autouse=True)
    def datetime_mock(self):
        now = datetime.now()
        with patch("modules.graph_lang.framework.scheduler_updater.datetime") as mock:
            mock.now.side_effect = lambda: now
            yield mock

    @pytest.fixture()
    def uuid(self):
        return fake.uuid4()

    def stop_updater_after_iteration(self):
        def stop_updater():
            self.updater.stop = True

        self.updater.set_post_step_callback(stop_updater)

    def test__no_event_done__scheduler_steps(self):
        self.stop_updater_after_iteration()

        self.updater.run()

        assert self.scheduler.get_all_events() == ["step"]

    def test__no_event_done__scheduler_sleeps_specified_time(self):
        self.stop_updater_after_iteration()

        sleep_at = self.datetime.now() + timedelta(seconds=5)

        self.scheduler.set_max_idle_datetime(sleep_at)
        self.updater.run()

        self.sleep.assert_called_once_with(5)

    def test__graph_created__scheduler__has_graph_created_event(self, uuid):
        fake_graph(id=uuid, save=True)

        self.scheduler.get_all_events() == [
            f"add graph {uuid}",
        ]

    def test__graph_updated__scheduler_recieves_graph_updated_event(self, uuid):
        graph = fake_graph(id=uuid, raw_graph_data="1", save=True)
        graph.save(force_update=True)

        assert self.scheduler.get_all_events() == [
            f"add graph {uuid}",
            f"update graph {uuid}",
        ]

    def test__graph_removed__scheduler_receives_graph_removed_event(self, uuid):
        graph = fake_graph(id=uuid, raw_graph_data="1", save=True)
        graph.delete()

        assert self.scheduler.get_all_events() == [
            f"add graph {uuid}",
            f"remove graph {uuid}",
        ]

    def test__buy_executed__scheduler_receives_transaction_executed_event(self, uuid):
        transaction = create_fake_transaction(
            investor=create_fake_investor(save=True),
            ticker=create_fake_instrument(save=True),
            price=100,
            is_buy=True,
        )
        transaction.save()
        inv_id = transaction.investor.id
        ins_id = transaction.ticker.id

        assert self.scheduler.get_all_events() == [f"buy {inv_id} {ins_id} 100"]

    def test__sell_executed__scheduler_receives_transaction_executed_event(self, uuid):
        transaction = create_fake_transaction(
            investor=create_fake_investor(save=True),
            ticker=create_fake_instrument(save=True),
            price=100,
            is_buy=False,
        )
        transaction.save()
        inv_id = transaction.investor.id
        ins_id = transaction.ticker.id

        assert self.scheduler.get_all_events() == [f"sell {inv_id} {ins_id} 100"]

    def test__prices_changed__scheduler_receives_prices_changed_event(self):
        self.stop_updater_after_iteration()
        prices = {
            "AAPL": get_fake_ohlc(ticker="AAPL", close=20),
            "GOGL": get_fake_ohlc(ticker="GOGL", close=30),
        }
        redis_client.set("latest_prices", json.dumps(prices))

        self.updater.run()

        assert self.scheduler.get_all_events() == [
            ("prices changed", {"AAPL": 20, "GOGL": 30}),
            "step",
        ]
        redis_client.delete("latest_prices")


def test__graph_exists_before_scheduler__all_graphs_added_on_init():
    uuid_1, uuid_2 = fake.uuid4(), fake.uuid4()
    fake_graph(uuid_1, save=True)
    fake_graph(uuid_2, save=True)

    scheduler = MockScheduler()
    updater = SchedulerUpdater(scheduler)

    assert scheduler.get_all_events() == [
        f"add graph {uuid_1}",
        f"add graph {uuid_2}",
    ]
