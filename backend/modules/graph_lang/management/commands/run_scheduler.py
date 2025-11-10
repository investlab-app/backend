from django.core.management.base import BaseCommand
from modules.graph_lang.framework.scheduler import Scheduler
from modules.graph_lang.framework.scheduler_updater import SchedulerUpdater


class Command(BaseCommand):
    def handle(self, *args, **options):
        scheduler = Scheduler()
        scheduler_updater = SchedulerUpdater(scheduler)
        scheduler_updater.run()
