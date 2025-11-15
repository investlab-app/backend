import decimal
import json
from datetime import datetime
from time import sleep

from django.db.models.signals import post_delete, post_save

from config.clients import redis_client
from modules.graph_lang.framework.scheduler import Scheduler
from modules.graph_lang.models import Graph
from modules.transactions.models import Transaction


class SchedulerUpdater:
    stop = False

    def __init__(self, scheduler):
        self.scheduler = scheduler or Scheduler()
        self._pre_step_callback = None
        self._post_step_callback = None
        self.get_all_graphs()
        post_save.connect(self.handle_graph_save, sender=Graph)
        post_delete.connect(self.handle_graph_delete, sender=Graph)
        post_save.connect(self.handle_transaction_execution, sender=Transaction)
        self.last_prices = {}
        self.received_prices = {}

    def get_all_graphs(self):
        ids = Graph.objects.values_list("id", flat=True)
        for id_ in ids:
            self.scheduler.add_graph(id_)

    def run(self):
        while not self.stop:
            if self._pre_step_callback:
                self._pre_step_callback()

            self._check_prices()
            now = datetime.now()
            next_step = self.scheduler.get_max_idle_datetime()
            sleep((next_step - now).seconds)
            self.scheduler.step()

            if self._post_step_callback:
                self._post_step_callback()

    def _check_prices(self):
        prices = redis_client.get("latest_prices")
        if prices is not None:
            prices = json.loads(prices)
            if self.last_prices != prices:
                self.last_prices = prices
                prices = {p: decimal.Decimal(prices[p]["close"]) for p in prices}
                self.scheduler.price_changed(prices)

    def handle_graph_save(self, sender, instance, created, **kwargs):
        if created:
            self.scheduler.add_graph(instance.id)
        else:
            self.scheduler.update_graph(instance.id)

    def handle_graph_delete(self, instance, **kwargs):
        self.scheduler.remove_graph(instance.id)

    def handle_transaction_execution(
        self, sender, instance: Transaction, created, **kwargs
    ):
        if created:
            if instance.is_buy:
                self.scheduler.buy_executed(
                    instance.investor.id,
                    instance.ticker.id,
                    instance.price,
                )
            else:
                self.scheduler.sell_executed(
                    instance.investor.id,
                    instance.ticker.id,
                    instance.price,
                )

    def set_post_step_callback(self, callback):
        self._post_step_callback = callback

    def set_pre_step_callback(self, callback):
        self._pre_step_callback = callback
