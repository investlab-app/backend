from datetime import datetime
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from time import sleep
from modules.graph_lang.models import Graph

class SchedulerUpdater:
    stop = False

    def __init__(self, scheduler):
        self.scheduler = scheduler
        self._pre_step_callback = None
        self._post_step_callback = None
        self.get_all_graphs()
        post_save.connect(self.handle_graph_save, sender=Graph)
        post_delete.connect(self.handle_graph_delete, sender=Graph)

    def get_all_graphs(self) -> list[Graph]:
        ids = Graph.objects.values_list('id', flat=True)
        for id in ids:
            self.scheduler.add_graph(id)

    def run(self):
        while not self.stop:

            if self._pre_step_callback:
                self._pre_step_callback()

            now = datetime.now()
            next_step = self.scheduler.get_max_idle_datetime()
            sleep((next_step - now).seconds)
            self.scheduler.step()

            if self._post_step_callback:
                self._post_step_callback()

    def handle_graph_save(self, sender, instance, created, **kwargs):
        if created:
            self.scheduler.add_graph(instance.id)
        else:
            self.scheduler.update_graph(instance.id)

    def handle_graph_delete(self, instance,  **kwargs):
        self.scheduler.remove_graph(instance.id)

    def set_post_step_callback(self, callback):
        self._post_step_callback = callback

    def set_pre_step_callback(self, callback):
        self._pre_step_callback = callback