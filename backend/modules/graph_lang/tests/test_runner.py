import pytest
import logging
from unittest.mock import Mock
from modules.graph_lang.framework.runner import Runner


class TestRunner:
    @pytest.fixture(autouse=True)
    def setup_runner(self):
        self.graph_provider = Mock()
        self.effect_handler = Mock()
        self.price_provider = Mock()
        self.runner = Runner(self.graph_provider, self.effect_handler, self.price_provider)

    @pytest.fixture
    def setup_root_node(self):
        self.root_node = Mock()
        self.graph_provider.get.return_value = self.root_node

        def execute(price_provider, effect_set):
            effect_set.add("effect1")

        self.root_node.execute.side_effect = execute

    def test_graph_not_exist__does_nothing(self):
        self.graph_provider.get.side_effect = Exception("not found")

        self.runner.run("missing_graph")

        self.graph_provider.get.assert_called_once_with("missing_graph")
        self.effect_handler.handle.assert_not_called()

    def test_prefetch_prices_called(self, setup_root_node):
        self.runner.run("graph1")
        self.root_node.prefetch_prices.assert_called_once_with(self.price_provider)

    def test_execute_called(self, setup_root_node):
        self.runner.run("graph1")
        self.root_node.execute.assert_called_once()
        args, _ = self.root_node.execute.call_args
        assert args[0] == self.price_provider

    def test_price_provider_cleared(self, setup_root_node):
        self.runner.run("graph1")
        self.price_provider.clear.assert_called_once()

    def test_effect_handler_called(self, setup_root_node):
        self.runner.run("graph1")
        self.effect_handler.handle.assert_called_once_with({'effect1'})
