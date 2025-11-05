from logging import Logger

logging = Logger(__name__)


class Runner:
    def __init__(self, graph_provider, effect_handler, price_provider):
        self._graph_provider = graph_provider
        self._effect_handler = effect_handler
        self._price_provider = price_provider

    def run(self, graph_id :str):
        effect_set = set()
        try:
            root_node = self._graph_provider.get(graph_id)
        except:
            logging.warning(f"Tried to run graph {graph_id} that does not exist")
            return

        root_node.prefetch_prices(self._price_provider)
        root_node.execute(self._price_provider, effect_set)
        self._price_provider.clear()

        self._effect_handler.handle(effect_set)