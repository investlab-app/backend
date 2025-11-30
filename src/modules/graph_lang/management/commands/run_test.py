from django.core.management.base import BaseCommand

from modules.graph_lang.framework.runner import Runner


class Command(BaseCommand):
    def handle(self, *args, **options):
        runner = Runner()
        runner.run("b3c7ff12-043a-472b-b3d0-3d694b55f377")
