from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand

from modules.core.management.mixins import CommandMessagesMixin
from modules.investors.models import Investor


class Command(CommandMessagesMixin, BaseCommand):

    def create_superuser(
        self,
        username='admin',
        email='admin@example.com',
        password='admin',
    ):
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username=username, email=email, password=password)
            self.print_success("Superuser created successfully. \n")
        else:
            self.print_info("Superuser already exists. \n")

    def create_investor(self, clerk_id: str) -> Investor:
        investor, created = Investor.objects.get_or_create(clerk_id=clerk_id)
        if created:
            self.print_success(f"Investor with clerk_id '{clerk_id}' created successfully. \n")
        else:
            self.print_info(f"Investor with clerk_id '{clerk_id}' already exists. \n")

        return investor

    def handle(self, *args, **options):
        self.create_superuser()

        call_command("seed_popular_instruments.py")
        investor = self.create_investor("user_2zvMzqYgWGJKhmnKL0mS4L4oFsP")  # my@wp.pl
