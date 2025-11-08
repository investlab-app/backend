from logging import Logger
from datetime import datetime

from modules.graph_lang.framework.nodes.node import Node, ExecutionContext

logging = Logger(__name__)


class Runner:
    def __init__(self, graph_provider, effect_handler, price_provider):
        self._graph_provider = graph_provider
        self._effect_handler = effect_handler
        self._price_provider = price_provider

    def run(self, graph_id :str, time_at :datetime):
        effect_set = set()
        try:
            root_node :Node = self._graph_provider.get(graph_id)
        except Exception as e:
            logging.warning(f"Tried to run graph {graph_id} that does not exist")
            return

        prices = root_node.calculate_needed_historical_prices()
        self._price_provider.prefetch_prices(prices)

        context = ExecutionContext(
            price_provider=self._price_provider,
            effects=effect_set,
            time_at=time_at
        )

        root_node.execute(context)


        self._price_provider.clear()

        self._effect_handler.handle(effect_set)