import pytest
from decimal import Decimal
import faker
from unittest.mock import MagicMock
from modules.graph_lang.framework.nodes import *
from modules.graph_lang.framework.nodes.node import ExecutionContext
from modules.graph_lang.framework.actions import BuySellAction
from modules.graph_lang.framework.runner import Runner

fake = faker.Faker()


class TestRunnerE2E:
    @pytest.fixture(autouse=True)
    def setup_runner(self):
        self.effect_handler = MagicMock()
        self.graph_provider = MagicMock()
        self.price_provider = MagicMock()

        self.runner = Runner(
            self.graph_provider,
            self.effect_handler,
            self.price_provider,
        )

    def setup_node(self, node):
        self.graph_provider.get.side_effect = lambda x: node

    def get_resulting_actions(self):
        return self.effect_handler.handle.call_args[0][0]

    def test__trigger_into_action(self):
        self.setup_node(
            CheckEveryNode({
                "in": BuySellAmountNode(
                    {"ticker": "AAPL", "amount": "20", "action": "buy"}
                )
            })
        )

        self.runner.run("graph", fake.date_time())

        assert self.get_resulting_actions() == {
            BuySellAction("buy", Decimal(20), "AAPL"),
        }