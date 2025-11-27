import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from modules.core.constants import DecimalConvertible
from modules.core.management.mixins import CommandMessagesMixin
from modules.instruments.models import Instrument
from modules.investors.models import AccountValueSnapshot, Asset, Investor
from modules.transactions.models import Transaction


class Command(CommandMessagesMixin, BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--investor-id",
            type=str,
            default="user_2zvMzqYgWGJKhmnKL0mS4L4oFsP",  # my@wp.pl
            help="Clerk ID for the investor to create/seed",
        )

    def create_superuser(
        self,
        username="admin",
        email="admin@example.com",
        password="admin",
    ):
        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(
                username=username, email=email, password=password
            )
            self.print_success("Superuser created successfully.")
        else:
            self.print_info("Superuser already exists.")

    def create_investor(
        self, clerk_id: str, balance: DecimalConvertible = 25_000
    ) -> Investor:
        investor, created = Investor.objects.get_or_create(
            clerk_id=clerk_id, defaults={"balance": Decimal(balance)}
        )
        if created:
            self.print_success(f"Investor(clerk_id='{clerk_id}') created successfully.")
        else:
            self.print_info(f"Investor(clerk_id='{clerk_id}') already exists.")

        return investor

    def update_assets(
        self, investor: Investor, instrument: Instrument, volume: DecimalConvertible
    ) -> Asset:
        asset = Asset.objects.filter(ticker=instrument, investor=investor).first()
        if asset:
            asset.volume = asset.volume + Decimal(volume)
            if asset.volume < 0:
                raise ValueError("Volume cannot be negative.")

            asset.save()

            self.print_success(
                f"Asset("
                f"\tinvestor='{investor.clerk_id}', "
                f"\tinstrument='{instrument.ticker}', "
                f"\tvolume={volume}"
                f") updated successfully."
            )
        else:
            if volume < 0:
                raise ValueError("Volume cannot be negative.")

            asset = Asset.objects.create(
                investor=investor,
                ticker=instrument,
                volume=Decimal(volume),
            )
            self.print_info(
                f"Asset("
                f"\tinvestor='{investor.clerk_id}', instrument='{instrument.ticker}'"
                f") to volume={volume} created."
            )

        return asset

    def create_transaction(
        self,
        investor: Investor,
        instrument: Instrument,
        volume: DecimalConvertible,
        price: DecimalConvertible,
        *,
        is_buy: bool,
    ) -> Transaction:
        transaction = Transaction.objects.create(
            investor=investor,
            ticker=instrument,
            volume=Decimal(volume),
            price=Decimal(price),
            is_buy=is_buy,
        )
        self.print_success(
            f"Transaction("
            f"\tinvestor='{investor.clerk_id}', "
            f"\tinstrument='{instrument.ticker}', volume={volume}, "
            f"\tprice={price}, is_buy={is_buy}"
            f") created successfully."
        )

        return transaction

    def create_account_value_snapshot(
        self,
        investor: Investor,
        timestamp: datetime | str,
        value: DecimalConvertible,
    ):
        snapshot = AccountValueSnapshot.objects.create(
            investor=investor,
            timestamp=timestamp,
            value=Decimal(value),
        )
        self.print_success(
            f"AccountValueSnapshot("
            f"\tinvestor='{investor.clerk_id}', "
            f"\ttimestamp='{timestamp}', "
            f"\tvalue={value}"
            f") created successfully."
        )

        return snapshot

    def handle(self, *args, **options):
        self.create_superuser()

        call_command("seed_popular_instruments")
        investor_id = options["investor_id"]
        investor = self.create_investor(investor_id)

        now = timezone.now()
        for days_ago in range(30, 0, -1):
            date = now - timedelta(days=days_ago)
            self.create_account_value_snapshot(
                investor=investor,
                timestamp=date,
                value=1000
                + days_ago * 10
                + random.randint(0, 50)
                + Decimal(random.randint(0, 99)) / Decimal(100),
            )

        tickers = {
            "AAPL": Decimal("259.13"),
            "MSFT": Decimal("529.24"),
            "GOOGL": Decimal("253.30"),
            "AMZN": Decimal("205.71"),
            "TSLA": Decimal("344.27"),
        }
        instruments = list(Instrument.objects.filter(ticker__in=list(tickers.keys())))
        if len(instruments) != len(tickers):
            self.print_error(
                "Not all specified instruments found. "
                "Ensure 'seed_popular_instruments' ran correctly.\n"
            )
            return

        for instrument in instruments:
            with transaction.atomic():
                buy_volume = Decimal(0)
                for _ in range(random.randint(1, 10)):
                    price_change = random.random() * -0.35
                    adjusted_price = tickers[instrument.ticker] * (
                        1 + Decimal(price_change)
                    )
                    volume = Decimal(random.randint(1, 100))
                    buy_volume += volume
                    self.create_transaction(
                        investor=investor,
                        instrument=instrument,
                        volume=volume,
                        price=adjusted_price,
                        is_buy=True,
                    )
                    self.update_assets(
                        investor=investor, instrument=instrument, volume=volume
                    )

                for _ in range(random.randint(1, 5)):
                    if buy_volume <= 0:
                        break

                    price_change = random.random() * 0.35
                    adjusted_price = tickers[instrument.ticker] * (
                        1 + Decimal(price_change)
                    )
                    volume = Decimal(random.randint(1, int(buy_volume)))
                    buy_volume -= volume
                    self.create_transaction(
                        investor=investor,
                        instrument=instrument,
                        volume=volume,
                        price=adjusted_price,
                        is_buy=False,
                    )
                    self.update_assets(
                        investor=investor, instrument=instrument, volume=-volume
                    )
