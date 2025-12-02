from decimal import Decimal

from django.db import transaction

from modules.investors.models import Asset
from modules.transactions.models import PartialTransaction, Transaction
from modules.transactions.schemas import TransactionParams


class ExecutiveTransactionService:
    @staticmethod
    def buy(params: TransactionParams):
        if params.volume <= 0:
            raise ValueError("Volume needs to be greater than 0")
        if params.price_per_unit <= 0:
            raise ValueError("Price needs to be greater than 0")
        total_cost = params.price_per_unit * params.volume
        if params.investor.balance < total_cost:
            raise ValueError("Investor doesn't have enough money")

        with transaction.atomic():
            buy_transaction = Transaction.objects.create(
                investor=params.investor,
                ticker=params.instrument,
                volume=params.volume,
                price=params.price_per_unit,
                is_buy=True,
            )

            asset, _ = Asset.objects.get_or_create(
                investor=params.investor,
                ticker=params.instrument,
                defaults={"volume": 0},
            )
            asset.volume += params.volume
            asset.save()

            PartialTransaction.objects.create(
                buy_transaction=buy_transaction, volume=params.volume
            )

            params.investor.balance -= total_cost
            params.investor.save()

        return buy_transaction

    @staticmethod
    def sell(params: TransactionParams):
        investor = params.investor
        instrument = params.instrument
        volume = params.volume
        if volume <= 0:
            raise ValueError("Volume needs to be greater than 0")
        if params.price_per_unit <= 0:
            raise ValueError("Price needs to be greater than 0")

        with transaction.atomic():
            asset = ExecutiveTransactionService._check_for_enough_assets(
                investor=investor, instrument=instrument, volume=volume
            )
            sell_transaction = Transaction.objects.create(
                investor=investor,
                ticker=instrument,
                volume=volume,
                price=params.price_per_unit,
                is_buy=False,
            )
            ExecutiveTransactionService._add_balance(
                investor, params.volume * params.price_per_unit
            )
            ExecutiveTransactionService._subtract_asset(asset, params.volume)
            ExecutiveTransactionService._handle_partial_transactions_after_sell(
                sell_transaction
            )

        return sell_transaction

    @staticmethod
    def _check_for_enough_assets(investor, instrument, volume):
        try:
            asset = Asset.objects.get(investor=investor, ticker=instrument)
        except Exception:
            raise ValueError("Investor doesn't have enough assets") from None

        if asset.volume < volume:
            raise ValueError("Investor doesn't have enough assets")
        return asset

    @staticmethod
    def _add_balance(investor, balance):
        investor.balance += balance
        investor.save()

    @staticmethod
    def _subtract_asset(asset, volume):
        asset.volume -= volume
        if asset.volume > 0:
            asset.save()
        else:
            asset.delete()

    @staticmethod
    def _handle_partial_transactions_after_sell(sell: Transaction):
        investor = sell.investor
        instrument = sell.ticker
        volume_left = sell.volume

        while volume_left > 0:
            open_partial = ExecutiveTransactionService._get_open_partial(
                investor=investor,
                instrument=instrument,
            )

            if volume_left >= open_partial.volume:
                ExecutiveTransactionService._close_partial_transaction(
                    sell=sell, partial_transaction=open_partial
                )
                volume_left -= open_partial.volume
            else:
                ExecutiveTransactionService._split_partial_transaction(
                    sell=sell,
                    partial_transaction=open_partial,
                    volume_closed=volume_left,
                )
                volume_left = 0

    @staticmethod
    def _get_open_partial(investor, instrument):
        return (
            PartialTransaction.objects.filter(
                sell_transaction=None,
                buy_transaction__investor=investor,
                buy_transaction__ticker=instrument,
            )
            .select_related("buy_transaction")
            .order_by("buy_transaction__timestamp")
            .first()
        )

    @staticmethod
    def get_open_partials(investor, instrument):
        return PartialTransaction.objects.filter(
            sell_transaction__isnull=True,
            buy_transaction__investor=investor,
            buy_transaction__ticker=instrument,
        )
    
    @staticmethod
    def get_closed_partials(investor, instrument):
        return PartialTransaction.objects.filter(
            sell_transaction__isnull=False,
            buy_transaction__investor=investor,
            buy_transaction__ticker=instrument,
        )
    
    @staticmethod
    def _close_partial_transaction(
        sell: Transaction, partial_transaction: PartialTransaction
    ):
        partial_transaction.sell_transaction = sell
        partial_transaction.save()

    @staticmethod
    def _split_partial_transaction(
        sell: Transaction,
        partial_transaction: PartialTransaction,
        volume_closed: Decimal,
    ):
        PartialTransaction.objects.create(
            buy_transaction=partial_transaction.buy_transaction,
            sell_transaction=sell,
            volume=volume_closed,
        )
        PartialTransaction.objects.create(
            buy_transaction=partial_transaction.buy_transaction,
            sell_transaction=None,
            volume=partial_transaction.volume - volume_closed,
        )
        partial_transaction.delete()
