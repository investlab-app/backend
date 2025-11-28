from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from modules.investors.models import Asset
from modules.transactions.models import Transaction
from modules.transactions.schemas import TransactionParams


class ExecuteTransactionService:
    def buy(self, params: TransactionParams):
        transaction_price = params.volume * params.price_per_unit
        if params.investor.balance < transaction_price:
            raise ValueError("Investor doesn't have enough balance")

        params.investor.balance -= transaction_price

        try:
            asset: Asset = Asset.objects.get(  # ty: ignore[invalid-assignment]
                investor=params.investor, ticker=params.instrument
            )
            asset.volume += params.volume
        except ObjectDoesNotExist:
            asset = Asset(
                investor=params.investor, ticker=params.instrument, volume=params.volume
            )

        with transaction.atomic():
            params.investor.save()
            Transaction.objects.create(
                investor=params.investor,
                ticker=params.instrument,
                volume=params.volume,
                price=params.volume * params.price_per_unit,
                is_buy=True,
            )
            asset.save()

    def sell(self, params: TransactionParams):
        try:
            asset: Asset = Asset.objects.get(  # ty: ignore[invalid-assignment]
                investor=params.investor, ticker=params.instrument
            )
        except ObjectDoesNotExist:
            raise ValueError("Asset does not exist.") from None

        if asset.volume < params.volume:
            raise ValueError("Not enough assets to sell.")

        transaction_price = params.volume * params.price_per_unit

        params.investor.balance += transaction_price
        asset.volume -= params.volume

        with transaction.atomic():
            params.investor.save()
            asset.save()
            Transaction.objects.create(
                investor=params.investor,
                ticker=params.instrument,
                volume=params.volume,
                price=transaction_price,
                is_buy=False,
            )
