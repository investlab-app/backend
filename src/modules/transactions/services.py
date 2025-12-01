from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction, models

from modules.investors.models import Asset
from modules.core.constants import PrecisionType
from modules.transactions.models import Transaction, PartialTransaction
from modules.transactions.schemas import TransactionParams


class ExecutiveTransactionService:
    @staticmethod
    def buy(params: TransactionParams):
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

            partial = PartialTransaction.objects.create(
                buy_transaction=buy_transaction, volume=params.volume
            )

            params.investor.balance -= total_cost
            params.investor.save()

        return buy_transaction

    @staticmethod
    def sell(params: TransactionParams):
        try:
            asset = Asset.objects.get(
                investor=params.investor, ticker=params.instrument
            )

            if asset.volume < params.volume:
                raise ValueError("Investor doesn't have enough assets")
        except:
            raise ValueError("Investor doesn't have enough assets")

        sell_transaction = Transaction.objects.create(
            investor=params.investor,
            ticker=params.instrument,
            volume=params.volume,
            price=params.price_per_unit,
            is_buy=False,
        )
        params.investor.balance += params.volume * params.price_per_unit
        params.investor.save()

        asset.volume -= params.volume
        if asset.volume > 0:
            asset.save()
        else:
            asset.delete()

        last_partial = PartialTransaction.objects.filter(
            sell_transaction=None,
            buy_transaction__investor=params.investor,
            buy_transaction__ticker=params.instrument,
        ).first()

        if params.volume < last_partial.volume:
            closed_partial = PartialTransaction(
                buy_transaction=last_partial.buy_transaction,
                sell_transaction=sell_transaction,
                volume=params.volume,
            )
            open_partial = PartialTransaction(
                buy_transaction=last_partial.buy_transaction,
                sell_transaction=None,
                volume=last_partial.volume - params.volume,
            )

            closed_partial.save()
            open_partial.save()

            last_partial.delete()
        else:
            last_partial.sell_transaction = sell_transaction
            last_partial.save()

        return sell_transaction

    # @staticmethod
    # def buy(params: TransactionParams):
    #     if params.investor.balance < params.price_per_unit * params.volume:
    #         raise ValueError("Investor doesn't have enough money")

    #     transaction = Transaction(
    #         investor=params.investor,
    #         ticker=params.instrument,
    #         volume=params.volume,
    #         price=params.price_per_unit,
    #         is_buy=True,
    #     )
    #     params.investor.balance -= params.price_per_unit * params.volume

    #     asset, _ = Asset.objects.get_or_create(
    #         investor=params.investor, ticker=params.instrument, defaults={"volume": Decimal(0)}
    #     )
    #     asset.volume += params.volume  # ty: ignore[unresolved-attribute]
    #     transaction.save()
    #     asset.save()
    #     params.investor.save()

    # @staticmethod
    # def sell(params: TransactionParams):
    #     investor = params.investor
    #     instrument = params.instrument
    #     volume = params.volume
    #     action_price = params.price_per_unit

    #     with transaction.atomic():
    #         asset = ExecutiveTransactionService._check_for_enough_assets(
    #             investor, instrument, volume
    #         )
    #         sell_transaction = Transaction(
    #             investor=investor,
    #             ticker = instrument,
    #             volume = volume,
    #             price = action_price,
    #             is_buy= False
    #         )

    #         investor.balance += volume * action_price
    #         asset.volume -= volume

    #         helpers = ExecutiveTransactionService._create_partial_transactions(sell_transaction)

    #         investor.save()
    #         sell_transaction.save()
    #         for helper in helpers:
    #             helper.save()

    #         if asset.volume < PrecisionType.volume.precision:
    #             asset.delete()
    #         else:
    #             asset.save()

    # @staticmethod
    # def _check_for_enough_assets(investor, instrument, volume):
    #     try:
    #         asset: Asset = Asset.objects.get(  # ty: ignore[invalid-assignment]
    #             investor=investor, ticker=instrument
    #         )
    #     except ObjectDoesNotExist:
    #         raise ValueError("Asset does not exist.") from None

    #     if asset.volume < volume:
    #         raise ValueError("Not enough assets to sell.")

    # @staticmethod
    # def _create_partial_transactions(sell_transaction :Transaction):
    #     helpers = []

    #     volume_remaining = sell_transaction.volume
    #     buy_transactions = ExecutiveTransactionService._get_buy_transactions(
    #         sell_transaction.investor, sell_transaction.ticker
    #     )

    #     for buy_transaction in buy_transactions:
    #         if volume_remaining == 0:
    #             break

    #         remaining_buy_volume = ExecutiveTransactionService._get_remaining_buy_volume(buy_transaction)
    #         if remaining_buy_volume <= 0:
    #             continue

    #         match_volume = min(volume_remaining, remaining_buy_volume)

    #         helpers.append(
    #             PartialTransaction(
    #                 buy_transaction=buy_transaction,
    #                 sell_transaction=sell_transaction,
    #                 volume=match_volume,
    #             )
    #         )
    #         volume_remaining -= match_volume

    #     return helpers

    # def _get_buy_transactions(investor, ticker):
    #     return Transaction.objects.filter(
    #         investor=investor, ticker=ticker, is_buy=True
    #     ).order_by("transaction_time")

    # def _get_remaining_buy_volume(buy_transaction):
    #     sold_volume_sum = (
    #         PartialTransaction.objects.filter(buy_transaction=buy_transaction).aggregate(
    #             sold_volume=models.Sum("volume")  # ty: ignore[unresolved-attribute]
    #         )["sold_volume"]
    #         or 0
    #     )

    #     return buy_transaction.volume - sold_volume_sum
