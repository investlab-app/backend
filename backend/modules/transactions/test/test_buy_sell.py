from dataclasses import dataclass

import pytest

from modules.investors.models import Asset, Investor
from modules.transactions.models import Transaction, TransactionHelper
from modules.transactions.services import buy, sell


@dataclass
class TransactionData:
    investor: Investor
    ticker: str
    volume: float
    price: float
    is_buy: bool

    def __eq__(self, value):
        if not isinstance(value, Transaction):
            return False
        return (
            self.investor == value.investor
            and self.ticker == value.ticker
            and self.volume == value.volume
            and self.price == value.transaction_price
            and self.is_buy == value.is_buy
        )


@dataclass
class AssetData:
    investor: Investor
    ticker: str
    volume: float

    def __eq__(self, value):
        if not isinstance(value, Asset):
            return False

        return (
            self.investor == value.investor
            and self.ticker == value.ticker
            and self.volume == value.volume
        )


@dataclass
class TransactionHelperData:
    buy_transaction: TransactionData
    sell_transaction: TransactionData
    volume: int

    def __eq__(self, value):
        if not isinstance(value, TransactionHelper):
            return
        return (
            self.buy_transaction == value.buy_transaction
            and self.sell_transaction == value.sell_transaction
            and self.volume == value.volume
        )


def get_investor(balance=0):
    investor = Investor.objects.create(clerk_id="asdf", balance=balance)
    return investor


def assert_db_state(
    transactions: list[TransactionData],
    transaction_helpers: list[TransactionHelperData],
    assets: list[AssetData],
):
    assert list(Transaction.objects.all()) == transactions
    assert list(TransactionHelper.objects.all()) == transaction_helpers
    assert list(Asset.objects.all()) == assets


@pytest.mark.django_db
def test_simple_buy():
    investor = get_investor(100)

    buy(investor=investor, ticker="A", volume=10, action_price=5)

    investor.refresh_from_db()
    assert investor.balance == 50
    assert_db_state(
        transactions=[TransactionData(investor, "A", volume=10, price=50, is_buy=True)],
        transaction_helpers=[],
        assets=[AssetData(investor, "A", 10)],
    )


@pytest.mark.django_db
def test_buy_sell_same_amount():
    investor = get_investor(100)

    buy(investor=investor, ticker="A", volume=10, action_price=5)
    sell(investor=investor, ticker="A", volume=10, action_price=7)

    transactions = [
        TransactionData(investor, "A", volume=10, price=50, is_buy=True),
        TransactionData(investor, "A", volume=10, price=70, is_buy=False),
    ]
    transaction_helpers = [
        TransactionHelperData(
            buy_transaction=transactions[0],
            sell_transaction=transactions[1],
            volume=10,
        )
    ]
    assets = []

    investor.refresh_from_db()
    assert investor.balance == 120
    assert_db_state(
        transactions=transactions,
        transaction_helpers=transaction_helpers,
        assets=assets,
    )


@pytest.mark.django_db
def test_two_buys_one_sell__sells_all():
    investor = get_investor(200)

    buy(investor=investor, ticker="A", volume=10, action_price=5)
    buy(investor=investor, ticker="A", volume=10, action_price=6)
    sell(investor=investor, ticker="A", volume=20, action_price=8)

    transactions = [
        TransactionData(investor, "A", volume=10, price=50, is_buy=True),
        TransactionData(investor, "A", volume=10, price=60, is_buy=True),
        TransactionData(investor, "A", volume=20, price=160, is_buy=False),
    ]
    transaction_helpers = [
        TransactionHelperData(
            buy_transaction=transactions[0], sell_transaction=transactions[2], volume=10
        ),
        TransactionHelperData(
            buy_transaction=transactions[1], sell_transaction=transactions[2], volume=10
        ),
    ]
    assets = []

    investor.refresh_from_db()
    assert investor.balance == 250

    assert_db_state(
        transactions=transactions,
        transaction_helpers=transaction_helpers,
        assets=assets,
    )


@pytest.mark.django_db
def test_one_buy_two_sells__sells_all():
    investor = get_investor(200)

    buy(investor=investor, ticker="A", volume=20, action_price=5)
    sell(investor=investor, ticker="A", volume=10, action_price=7)
    sell(investor=investor, ticker="A", volume=10, action_price=8)

    transactions = [
        TransactionData(investor, "A", volume=20, price=100, is_buy=True),
        TransactionData(investor, "A", volume=10, price=70, is_buy=False),
        TransactionData(investor, "A", volume=10, price=80, is_buy=False),
    ]
    transaction_helpers = [
        TransactionHelperData(
            buy_transaction=transactions[0], sell_transaction=transactions[1], volume=10
        ),
        TransactionHelperData(
            buy_transaction=transactions[0], sell_transaction=transactions[2], volume=10
        ),
    ]
    assets = []

    investor.refresh_from_db()
    assert investor.balance == 250

    assert_db_state(
        transactions=transactions,
        transaction_helpers=transaction_helpers,
        assets=assets,
    )


@pytest.mark.django_db
def test_one_buy_one_sell__sells_partial_action():
    investor = get_investor(100)

    buy(investor=investor, ticker="A", volume=10, action_price=5)
    sell(investor=investor, ticker="A", volume=5, action_price=8)

    transactions = [
        TransactionData(investor, "A", volume=10, price=50, is_buy=True),
        TransactionData(investor, "A", volume=5, price=40, is_buy=False),
    ]
    transaction_helpers = [
        TransactionHelperData(
            buy_transaction=transactions[0], sell_transaction=transactions[1], volume=5
        )
    ]
    assets = [AssetData(investor, "A", 5)]

    investor.refresh_from_db()
    assert investor.balance == 90

    assert_db_state(
        transactions=transactions,
        transaction_helpers=transaction_helpers,
        assets=assets,
    )


@pytest.mark.django_db
def test_two_buys_three_sells__all_transactions_overlap__asset_remains():
    investor = get_investor(500)

    buy(investor=investor, ticker="A", volume=10, action_price=10)
    buy(investor=investor, ticker="A", volume=15, action_price=12)
    sell(investor=investor, ticker="A", volume=5, action_price=15)
    sell(investor=investor, ticker="A", volume=10, action_price=16)
    sell(investor=investor, ticker="A", volume=5, action_price=14)

    transactions = [
        TransactionData(investor, "A", volume=10, price=100, is_buy=True),
        TransactionData(investor, "A", volume=15, price=180, is_buy=True),
        TransactionData(investor, "A", volume=5, price=75, is_buy=False),
        TransactionData(investor, "A", volume=10, price=160, is_buy=False),
        TransactionData(investor, "A", volume=5, price=70, is_buy=False),
    ]
    transaction_helpers = [
        TransactionHelperData(
            buy_transaction=transactions[0], sell_transaction=transactions[2], volume=5
        ),
        TransactionHelperData(
            buy_transaction=transactions[0], sell_transaction=transactions[3], volume=5
        ),
        TransactionHelperData(
            buy_transaction=transactions[1], sell_transaction=transactions[3], volume=5
        ),
        TransactionHelperData(
            buy_transaction=transactions[1], sell_transaction=transactions[4], volume=5
        ),
    ]
    assets = [AssetData(investor, "A", 5)]

    investor.refresh_from_db()
    assert investor.balance == 525

    assert_db_state(
        transactions=transactions,
        transaction_helpers=transaction_helpers,
        assets=assets,
    )


@pytest.mark.django_db
def test_three_buys_two_sells__all_transactions_overlap__asset_remains():
    investor = get_investor(400)

    buy(investor=investor, ticker="A", volume=10, action_price=10)
    buy(investor=investor, ticker="A", volume=10, action_price=12)
    buy(investor=investor, ticker="A", volume=10, action_price=14)
    sell(investor=investor, ticker="A", volume=15, action_price=15)
    sell(investor=investor, ticker="A", volume=10, action_price=16)

    transactions = [
        TransactionData(investor, "A", volume=10, price=100, is_buy=True),
        TransactionData(investor, "A", volume=10, price=120, is_buy=True),
        TransactionData(investor, "A", volume=10, price=140, is_buy=True),
        TransactionData(investor, "A", volume=15, price=225, is_buy=False),
        TransactionData(investor, "A", volume=10, price=160, is_buy=False),
    ]
    transaction_helpers = [
        TransactionHelperData(
            buy_transaction=transactions[0], sell_transaction=transactions[3], volume=10
        ),
        TransactionHelperData(
            buy_transaction=transactions[1], sell_transaction=transactions[3], volume=5
        ),
        TransactionHelperData(
            buy_transaction=transactions[1], sell_transaction=transactions[4], volume=5
        ),
        TransactionHelperData(
            buy_transaction=transactions[2], sell_transaction=transactions[4], volume=5
        ),
    ]
    assets = [AssetData(investor, "A", 5)]

    investor.refresh_from_db()
    assert investor.balance == 425

    assert_db_state(
        transactions=transactions,
        transaction_helpers=transaction_helpers,
        assets=assets,
    )


@pytest.mark.django_db
def test_sell_not_enough_assets():
    investor = get_investor(100)
    buy(investor=investor, ticker="A", volume=10, action_price=5)

    with pytest.raises(RuntimeError):
        sell(investor=investor, ticker="A", volume=15, action_price=8)


@pytest.mark.django_db
def test_sell_asset_does_not_exist():
    investor = get_investor(100)

    with pytest.raises(RuntimeError):
        sell(investor=investor, ticker="A", volume=10, action_price=8)
