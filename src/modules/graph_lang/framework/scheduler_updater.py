import decimal
from datetime import datetime
from time import sleep
from uuid import UUID

from modules.graph_lang.framework.scheduler import Scheduler
from modules.graph_lang.models import Graph
from modules.prices.services import LatestPriceService
from modules.transactions.models import Transaction


class SchedulerUpdater:
    stop = False

    graph_ids: dict[UUID, datetime]
    transaction_ids: list[UUID]

    def __init__(
        self, scheduler, latest_price_service: LatestPriceService | None = None
    ):
        self._latest_price_service = latest_price_service or LatestPriceService()
        self.scheduler = scheduler or Scheduler()

        self.graph_ids = {}
        self.transaction_ids = []
        self._check_new_graphs()
        self._fill_transactions()

        self._pre_step_callback = None
        self._post_step_callback = None
        self.last_prices = {}
        self.received_prices = {}

    def run(self):
        while not self.stop:
            if self._pre_step_callback:
                self._pre_step_callback()

            self._check_new_graphs()
            self._check_updated_graphs()
            self._check_removed_graphs()
            self._check_new_transactions()
            self._check_prices()

            now = datetime.now()
            next_step = self.scheduler.get_max_idle_datetime()
            sleep((next_step - now).seconds)
            self.scheduler.step()

            if self._post_step_callback:
                self._post_step_callback()

    def _check_new_graphs(self):
        current_ids = self.graph_ids.keys()
        new_graphs = Graph.objects.exclude(id__in=current_ids)

        for graph in new_graphs:
            self.graph_ids[graph.id] = graph.updated_at
            self.scheduler.add_graph(graph.id)

    def _fill_transactions(self):
        for t in Transaction.objects.all():
            self.transaction_ids.append(t.id)

    def _check_updated_graphs(self):
        current_ids = self.graph_ids.keys()
        current_graphs = Graph.objects.filter(id__in=current_ids)

        for graph in current_graphs:
            if graph.updated_at != self.graph_ids[graph.id]:
                self.graph_ids[graph.id] = graph.updated_at
                self.scheduler.update_graph(graph.id)

    def _check_removed_graphs(self):
        removed_ids = []
        for id_ in self.graph_ids:
            if not Graph.objects.filter(id=id_).exists():
                self.scheduler.remove_graph(id_)
                removed_ids.append(id_)

        for id_ in removed_ids:
            self.graph_ids.pop(id_)

    def _check_new_transactions(self):
        new_transactions = Transaction.objects.exclude(id__in=self.transaction_ids)
        for transaction in new_transactions:
            self.transaction_ids.append(transaction.id)
            if transaction.is_buy:
                self.scheduler.buy_executed(
                    transaction.investor.id,
                    transaction.ticker.ticker,
                    transaction.volume,
                )
            else:
                self.scheduler.sell_executed(
                    transaction.investor.id,
                    transaction.ticker.ticker,
                    transaction.volume,
                )

    def _check_prices(self):
        prices = self._latest_price_service.get_prices()
        if self.last_prices != prices:
            self.last_prices = prices
            prices = {p: decimal.Decimal(prices[p]) for p in prices}
            self.scheduler.price_changed(prices)

    def set_post_step_callback(self, callback):
        self._post_step_callback = callback

    def set_pre_step_callback(self, callback):
        self._pre_step_callback = callback
