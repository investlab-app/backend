from decimal import Decimal

from django import db

from modules.instruments.models import Instrument
from modules.investors.models import Asset, Investor
from modules.transactions.models import Transaction, TransactionHelper


def buy(investor: Investor, ticker: Instrument, volume: Decimal, action_price: Decimal):
    assert isinstance(volume, Decimal)
    assert isinstance(action_price, Decimal)
    _check_investor_has_enough_money(investor, action_price * volume)

    transaction = Transaction(
        investor=investor,
        ticker=ticker,
        volume=volume,
        transaction_price=action_price * volume,
        is_buy=True,
    )
    investor.balance -= transaction.transaction_price

    asset = _add_volume_to_asset(investor, ticker, volume)
    _save_to_db(transaction, asset, investor)


def _check_investor_has_enough_money(investor, min_money):
    if investor.balance < min_money:
        raise RuntimeError("Trying to make buy transaction without enough money")


def _add_volume_to_asset(investor, ticker, volume):
    asset, _ = Asset.objects.get_or_create(
        investor=investor, ticker=ticker, defaults={"volume": Decimal(0)}
    )
    asset.volume += volume
    return asset


def _save_to_db(transaction, asset, investor):
    with db.transaction.atomic():
        transaction.save()
        asset.save()
        investor.save()


def sell(investor, ticker, volume, action_price):
    asset = _check_for_enough_assets(investor, ticker, volume)

    sell_transaction = Transaction(
        investor=investor,
        ticker=ticker,
        volume=volume,
        transaction_price=action_price * volume,
        is_buy=False,
    )

    investor.balance += sell_transaction.transaction_price
    asset.volume -= volume

    helpers = _create_transaction_helpers(sell_transaction)

    _sell_save(investor, sell_transaction, asset, helpers)


def _check_for_enough_assets(investor, ticker, volume):
    try:
        asset = Asset.objects.get(investor=investor, ticker=ticker)
        if asset.volume < volume:
            raise RuntimeError("Not enough assets to sell")
        return asset
    except Asset.DoesNotExist:
        raise RuntimeError("No assets to sell") from None


def _create_transaction_helpers(sell_transaction):
    helpers = []

    volume_remaining = sell_transaction.volume
    buy_transactions = _get_buy_transactions(
        sell_transaction.investor, sell_transaction.ticker
    )

    for buy_transaction in buy_transactions:
        if volume_remaining == 0:
            break

        remaining_buy_volume = _get_remaining_buy_volume(buy_transaction)
        if remaining_buy_volume <= 0:
            continue

        match_volume = min(volume_remaining, remaining_buy_volume)

        helpers.append(
            TransactionHelper(
                buy_transaction=buy_transaction,
                sell_transaction=sell_transaction,
                volume=match_volume,
            )
        )
        volume_remaining -= match_volume

    return helpers


def _get_buy_transactions(investor, ticker):
    return Transaction.objects.filter(
        investor=investor, ticker=ticker, is_buy=True
    ).order_by("transaction_time")


def _get_remaining_buy_volume(buy_transaction):
    sold_volume_sum = (
        TransactionHelper.objects.filter(buy_transaction=buy_transaction).aggregate(
            sold_volume=db.models.Sum("volume")
        )["sold_volume"]
        or 0
    )

    return buy_transaction.volume - sold_volume_sum


def _sell_save(investor, sell_transaction, asset, helpers):
    with db.transaction.atomic():
        investor.save()
        sell_transaction.save()
        for helper in helpers:
            helper.save()

        if asset.volume == 0:
            asset.delete()
        else:
            asset.save()
