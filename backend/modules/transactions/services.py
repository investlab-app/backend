from decimal import Decimal

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from pydantic import BaseModel

from modules.instruments.models import Instrument
from modules.investors.models import Asset, Investor
from modules.transactions.models import Transaction


class TransactionParams(BaseModel):
    investor: Investor
    ticker: Instrument
    volume: Decimal
    action_price: Decimal

    class Config:
        arbitrary_types_allowed = True


class ExecuteTransactionService:
    def buy(self, args: TransactionParams):
        transaction_price = args.volume * args.action_price
        if args.investor.balance < transaction_price:
            raise ValueError("Investor doesn't have enough balance")

        args.investor.balance -= transaction_price

        try:
            asset: Asset = Asset.objects.get(  # ty: ignore[invalid-assignment]
                investor=args.investor, ticker=args.ticker
            )
            asset.volume += args.volume
        except ObjectDoesNotExist:
            asset = Asset(
                investor=args.investor, ticker=args.ticker, volume=args.volume
            )

        with transaction.atomic():
            args.investor.save()
            Transaction.objects.create(
                investor=args.investor,
                ticker=args.ticker,
                volume=args.volume,
                transaction_price=args.volume * args.action_price,
                is_buy=True,
            )
            asset.save()

    def sell(self, args: TransactionParams):
        try:
            asset: Asset = Asset.objects.get(  # ty: ignore[invalid-assignment]
                investor=args.investor, ticker=args.ticker
            )
        except ObjectDoesNotExist:
            raise ValueError("Asset does not exist.") from None

        if asset.volume < args.volume:
            raise ValueError("Not enough assets to sell.")

        transaction_price = args.volume * args.action_price

        args.investor.balance += transaction_price
        asset.volume -= args.volume

        with transaction.atomic():
            args.investor.save()
            asset.save()
            Transaction.objects.create(
                investor=args.investor,
                ticker=args.ticker,
                volume=args.volume,
                transaction_price=transaction_price,
                is_buy=False,
            )
