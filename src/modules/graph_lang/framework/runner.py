import logging
from datetime import datetime

from modules.graph_lang.framework.action_handler import ActionHandler
from modules.graph_lang.framework.builder import GraphBuilder
from modules.graph_lang.framework.nodes.node import ExecutionContext, Node
from modules.graph_lang.framework.parser import GraphData
from modules.graph_lang.framework.price_provider import PriceProvider
from modules.graph_lang.models import Graph

logger = logging.getLogger(__name__)


# TODO rename to GraphRunner
class Runner:
    def __init__(
        self,
        builder: GraphBuilder | None = None,
        action_handler: ActionHandler | None = None,
    ):
        self._graph_builder = builder or GraphBuilder()
        self._action_handler = action_handler or ActionHandler()

    def run(
        self,
        graph_id: str,
        time_at: datetime | None = None,
        price_provider: PriceProvider | None = None,
    ):
        time_at = time_at or datetime.now()
        effect_set = set()

        try:
            graph = Graph.objects.get(id=graph_id)
        except Exception:
            logger.warning("Tried to run graph %s that does not exist", graph_id)
            return

        graph_data = GraphData.model_validate(graph.graph_data)
        root_node: Node = self._graph_builder.build(graph_data)
        price_provider = price_provider or PriceProvider()
        prices_needed = root_node.calculate_needed_historical_prices()
        price_provider.prefetch_data(prices_needed, time_at)

        context = ExecutionContext(
            price_provider=price_provider, effects=effect_set, time_at=time_at
        )

        try:
            root_node.execute(context)
        except Exception:
            logger.exception("Graph executed with errors")
            return {}

        graph = Graph.objects.get(id=graph_id)
        self._action_handler.handle(
            investor_id=graph.investor.id,
            graph_id=graph_id,
            action_set=context.effects,
        )

        return effect_set
