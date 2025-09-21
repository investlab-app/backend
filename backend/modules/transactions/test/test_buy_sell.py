from dataclasses import dataclass
from decimal import Decimal

import pytest
from pydantic import BaseModel, ConfigDict

from modules.core.defaults import PrecisionType
from modules.instruments.models import Instrument
from modules.investors.models import Asset, Investor
from modules.transactions.models import Transaction, TransactionHelper
from modules.transactions.services.buy_sell import buy, sell


class TransactionData(BaseModel):
    investor: Investor
    ticker: Instrument
    volume: Decimal
    price: Decimal
    is_buy: bool

    def __eq__(self, value):
        if not isinstance(value, Transaction):
            return False
        return (
            self.investor == value.investor
            and self.ticker == value.ticker
            and abs(self.volume - value.volume) < PrecisionType.volume.precision
            and abs(self.price - value.transaction_price)
            < PrecisionType.price.precision
            and self.is_buy == value.is_buy
        )

    model_config = ConfigDict(arbitrary_types_allowed=True)


@dataclass
class AssetData:
    investor: Investor
    ticker: Instrument
    volume: Decimal

    def __eq__(self, value):
        if not isinstance(value, Asset):
            return False

        return (
            self.investor == value.investor
            and self.ticker == value.ticker
            and abs(self.volume - value.volume) < PrecisionType.volume.precision
        )

    model_config = ConfigDict(arbitrary_types_allowed=True)


@dataclass
class TransactionHelperData:
    buy_transaction: TransactionData
    sell_transaction: TransactionData
    volume: Decimal

    def __eq__(self, value):
        if not isinstance(value, TransactionHelper):
            return False
        return (
            self.buy_transaction == value.buy_transaction
            and self.sell_transaction == value.sell_transaction
            and abs(self.volume - value.volume) < PrecisionType.volume.precision
        )

    model_config = ConfigDict(arbitrary_types_allowed=True)


def get_investor(balance=0):
    investor = Investor.objects.create(clerk_id="asdf", balance=Decimal(balance))
    return investor


@pytest.fixture
def ticker():
    return Instrument.objects.create(ticker="AAPL", active=True)


def assert_db_state(
    transactions: list[TransactionData],
    transaction_helpers: list[TransactionHelperData],
    assets: list[AssetData],
):
    print(list(Transaction.objects.all()), transactions)
    assert list(Transaction.objects.all()) == transactions
    assert list(TransactionHelper.objects.all()) == transaction_helpers
    assert list(Asset.objects.all()) == assets


@pytest.mark.django_db
def test_simple_buy(ticker):
    investor = get_investor(100)

    buy(investor=investor, ticker=ticker, volume=Decimal(10), action_price=Decimal(5))

    investor.refresh_from_db()
    assert investor.balance == 50
    assert_db_state(
        transactions=[
            TransactionData(
                investor=investor,
                ticker=ticker,
                volume=Decimal(10),
                price=Decimal(50),
                is_buy=True,
            )
        ],
        transaction_helpers=[],
        assets=[AssetData(investor, ticker, Decimal(10))],
    )


@pytest.mark.django_db
def test_buy_sell_same_amount(ticker):
    investor = get_investor(100)

    buy(investor=investor, ticker=ticker, volume=Decimal(10), action_price=Decimal(5))
    sell(investor=investor, ticker=ticker, volume=Decimal(10), action_price=Decimal(7))

    transactions = [
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(10),
            price=Decimal(50),
            is_buy=True,
        ),
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(10),
            price=Decimal(70),
            is_buy=False,
        ),
    ]
    transaction_helpers = [
        TransactionHelperData(
            buy_transaction=transactions[0],
            sell_transaction=transactions[1],
            volume=Decimal(10),
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
def test_two_buys_one_sell__sells_all(ticker):
    investor = get_investor(200)

    buy(investor=investor, ticker=ticker, volume=Decimal(10), action_price=Decimal(5))
    buy(investor=investor, ticker=ticker, volume=Decimal(10), action_price=Decimal(6))
    sell(investor=investor, ticker=ticker, volume=Decimal(20), action_price=Decimal(8))

    transactions = [
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(10),
            price=Decimal(50),
            is_buy=True,
        ),
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(10),
            price=Decimal(60),
            is_buy=True,
        ),
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(20),
            price=Decimal(160),
            is_buy=False,
        ),
    ]
    transaction_helpers = [
        TransactionHelperData(
            buy_transaction=transactions[0],
            sell_transaction=transactions[2],
            volume=Decimal(10),
        ),
        TransactionHelperData(
            buy_transaction=transactions[1],
            sell_transaction=transactions[2],
            volume=Decimal(10),
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
def test_one_buy_two_sells__sells_all(ticker):
    investor = get_investor(200)

    buy(investor=investor, ticker=ticker, volume=Decimal(20), action_price=Decimal(5))
    sell(investor=investor, ticker=ticker, volume=Decimal(10), action_price=Decimal(7))
    sell(investor=investor, ticker=ticker, volume=Decimal(10), action_price=Decimal(8))

    transactions = [
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(20),
            price=Decimal(100),
            is_buy=True,
        ),
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(10),
            price=Decimal(70),
            is_buy=False,
        ),
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(10),
            price=Decimal(80),
            is_buy=False,
        ),
    ]
    transaction_helpers = [
        TransactionHelperData(
            buy_transaction=transactions[0],
            sell_transaction=transactions[1],
            volume=Decimal(10),
        ),
        TransactionHelperData(
            buy_transaction=transactions[0],
            sell_transaction=transactions[2],
            volume=Decimal(10),
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
def test_one_buy_one_sell__sells_partial_action(ticker):
    investor = get_investor(100)

    buy(investor=investor, ticker=ticker, volume=Decimal(10), action_price=Decimal(5))
    sell(investor=investor, ticker=ticker, volume=Decimal(5), action_price=Decimal(8))

    transactions = [
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(10),
            price=Decimal(50),
            is_buy=True,
        ),
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(5),
            price=Decimal(40),
            is_buy=False,
        ),
    ]
    transaction_helpers = [
        TransactionHelperData(
            buy_transaction=transactions[0],
            sell_transaction=transactions[1],
            volume=Decimal(5),
        )
    ]
    assets = [AssetData(investor, ticker, Decimal(5))]

    investor.refresh_from_db()
    assert investor.balance == 90

    assert_db_state(
        transactions=transactions,
        transaction_helpers=transaction_helpers,
        assets=assets,
    )


@pytest.mark.django_db
def test_two_buys_three_sells__all_transactions_overlap__asset_remains(ticker):
    investor = get_investor(500)

    buy(investor=investor, ticker=ticker, volume=Decimal(10), action_price=Decimal(10))
    buy(investor=investor, ticker=ticker, volume=Decimal(15), action_price=Decimal(12))
    sell(investor=investor, ticker=ticker, volume=Decimal(5), action_price=Decimal(15))
    sell(investor=investor, ticker=ticker, volume=Decimal(10), action_price=Decimal(16))
    sell(investor=investor, ticker=ticker, volume=Decimal(5), action_price=Decimal(14))

    transactions = [
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(10),
            price=Decimal(100),
            is_buy=True,
        ),
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(15),
            price=Decimal(180),
            is_buy=True,
        ),
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(5),
            price=Decimal(75),
            is_buy=False,
        ),
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(10),
            price=Decimal(160),
            is_buy=False,
        ),
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(5),
            price=Decimal(70),
            is_buy=False,
        ),
    ]
    transaction_helpers = [
        TransactionHelperData(
            buy_transaction=transactions[0],
            sell_transaction=transactions[2],
            volume=Decimal(5),
        ),
        TransactionHelperData(
            buy_transaction=transactions[0],
            sell_transaction=transactions[3],
            volume=Decimal(5),
        ),
        TransactionHelperData(
            buy_transaction=transactions[1],
            sell_transaction=transactions[3],
            volume=Decimal(5),
        ),
        TransactionHelperData(
            buy_transaction=transactions[1],
            sell_transaction=transactions[4],
            volume=Decimal(5),
        ),
    ]
    assets = [AssetData(investor, ticker, Decimal(5))]

    investor.refresh_from_db()
    assert investor.balance == 525

    assert_db_state(
        transactions=transactions,
        transaction_helpers=transaction_helpers,
        assets=assets,
    )


@pytest.mark.django_db
def test_three_buys_two_sells__all_transactions_overlap__asset_remains(ticker):
    investor = get_investor(400)

    buy(investor=investor, ticker=ticker, volume=Decimal(10), action_price=Decimal(10))
    buy(investor=investor, ticker=ticker, volume=Decimal(10), action_price=Decimal(12))
    buy(investor=investor, ticker=ticker, volume=Decimal(10), action_price=Decimal(14))
    sell(investor=investor, ticker=ticker, volume=Decimal(15), action_price=Decimal(15))
    sell(investor=investor, ticker=ticker, volume=Decimal(10), action_price=Decimal(16))

    transactions = [
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(10),
            price=Decimal(100),
            is_buy=True,
        ),
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(10),
            price=Decimal(120),
            is_buy=True,
        ),
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(10),
            price=Decimal(140),
            is_buy=True,
        ),
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(15),
            price=Decimal(225),
            is_buy=False,
        ),
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=Decimal(10),
            price=Decimal(160),
            is_buy=False,
        ),
    ]
    transaction_helpers = [
        TransactionHelperData(
            buy_transaction=transactions[0],
            sell_transaction=transactions[3],
            volume=Decimal(10),
        ),
        TransactionHelperData(
            buy_transaction=transactions[1],
            sell_transaction=transactions[3],
            volume=Decimal(5),
        ),
        TransactionHelperData(
            buy_transaction=transactions[1],
            sell_transaction=transactions[4],
            volume=Decimal(5),
        ),
        TransactionHelperData(
            buy_transaction=transactions[2],
            sell_transaction=transactions[4],
            volume=Decimal(5),
        ),
    ]
    assets = [AssetData(investor, ticker, Decimal(5))]

    investor.refresh_from_db()
    assert investor.balance == 425

    assert_db_state(
        transactions=transactions,
        transaction_helpers=transaction_helpers,
        assets=assets,
    )


@pytest.mark.django_db
def test_sell_not_enough_assets(ticker):
    investor = get_investor(100)
    buy(investor=investor, ticker=ticker, volume=Decimal(10), action_price=Decimal(5))

    with pytest.raises(RuntimeError):
        sell(
            investor=investor,
            ticker=ticker,
            volume=Decimal(15),
            action_price=Decimal(8),
        )


@pytest.mark.django_db
def test_buy_not_enough_balance(ticker):
    investor = get_investor(100)

    with pytest.raises(RuntimeError):
        buy(
            investor=investor,
            ticker=ticker,
            volume=Decimal(2),
            action_price=Decimal(90),
        )


@pytest.mark.django_db
def test_sell_asset_does_not_exist(ticker):
    investor = get_investor(100)

    with pytest.raises(RuntimeError):
        sell(
            investor=investor,
            ticker=ticker,
            volume=Decimal(10),
            action_price=Decimal(8),
        )


@pytest.mark.django_db
def test_buy_partial_volume(ticker):
    balance = 100
    investor = get_investor(balance)
    volume = Decimal(0.5)
    price = Decimal(150)

    buy(
        investor=investor,
        ticker=ticker,
        volume=volume,
        action_price=price,
    )

    transactions = [
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=volume,
            price=(volume * price),
            is_buy=True,
        )
    ]
    transaction_helpers = []
    assets = [
        AssetData(
            investor=investor,
            ticker=ticker,
            volume=volume,
        )
    ]

    investor.refresh_from_db()
    assert (
        abs(investor.balance - (Decimal(balance) - (volume * price)))
        < PrecisionType.price.precision
    )

    assert_db_state(
        transactions=transactions,
        transaction_helpers=transaction_helpers,
        assets=assets,
    )


@pytest.mark.django_db
def test_sell_partial_volume(ticker):
    balance = 100
    investor = get_investor(balance)
    buy_volume = Decimal(0.24)
    buy_price = Decimal(235.5)
    sell_volume = Decimal(0.108)
    sell_price = Decimal(300.90)

    buy(
        investor=investor,
        ticker=ticker,
        volume=buy_volume,
        action_price=buy_price,
    )
    sell(
        investor=investor,
        ticker=ticker,
        volume=sell_volume,
        action_price=sell_price,
    )

    transactions = [
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=buy_volume,
            price=(buy_volume * buy_price),
            is_buy=True,
        ),
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=sell_volume,
            price=(sell_volume * sell_price),
            is_buy=False,
        ),
    ]
    transaction_helpers = [
        TransactionHelperData(
            buy_transaction=transactions[0],
            sell_transaction=transactions[1],
            volume=sell_volume,
        )
    ]
    assets = [
        AssetData(
            investor=investor,
            ticker=ticker,
            volume=buy_volume - sell_volume,
        )
    ]

    investor.refresh_from_db()
    assert (
        abs(
            investor.balance
            - (Decimal(balance) - (buy_volume * buy_price) + (sell_volume * sell_price))
        )
        < PrecisionType.price.precision
    )

    assert_db_state(
        transactions=transactions,
        transaction_helpers=transaction_helpers,
        assets=assets,
    )


@pytest.mark.django_db
def test_buy_sell_same_partial_volume(ticker):
    balance = 100.80
    investor = get_investor(balance)
    volume = Decimal(0.2450009)
    buy_price = Decimal(235.5)
    sell_price = Decimal(300.90)

    buy(
        investor=investor,
        ticker=ticker,
        volume=volume,
        action_price=buy_price,
    )

    sell(
        investor=investor,
        ticker=ticker,
        volume=volume,
        action_price=sell_price,
    )
    transactions = [
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=volume,
            price=(volume * buy_price),
            is_buy=True,
        ),
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=volume,
            price=(volume * sell_price),
            is_buy=False,
        ),
    ]
    transaction_helpers = [
        TransactionHelperData(
            buy_transaction=transactions[0],
            sell_transaction=transactions[1],
            volume=volume,
        )
    ]
    assets = []

    investor.refresh_from_db()
    assert (
        abs(
            investor.balance
            - (Decimal(balance) - (volume * buy_price) + (volume * sell_price))
        )
        < PrecisionType.price.precision
    )

    assert_db_state(
        transactions=transactions,
        transaction_helpers=transaction_helpers,
        assets=assets,
    )


@pytest.mark.django_db
def test_very_large_buy_and_sell(ticker):
    balance = 100_000_000_000
    investor = get_investor(balance)
    buy_volume = Decimal(100_000_000_000)
    buy_price = Decimal(0.05)
    sell_price = Decimal(0.1)

    buy(
        investor=investor,
        ticker=ticker,
        volume=buy_volume,
        action_price=buy_price,
    )

    sell(
        investor=investor,
        ticker=ticker,
        volume=buy_volume,
        action_price=sell_price,
    )

    transactions = [
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=buy_volume,
            price=(buy_volume * buy_price),
            is_buy=True,
        ),
        TransactionData(
            investor=investor,
            ticker=ticker,
            volume=buy_volume,
            price=(buy_volume * sell_price),
            is_buy=False,
        ),
    ]

    transaction_helpers = [
        TransactionHelperData(
            buy_transaction=transactions[0],
            sell_transaction=transactions[1],
            volume=buy_volume,
        )
    ]
    assets = []

    investor.refresh_from_db()
    assert (
        abs(
            investor.balance
            - (Decimal(balance) - (buy_volume * buy_price) + (buy_volume * sell_price))
        )
        < PrecisionType.price.precision
    )

    assert_db_state(
        transactions=transactions,
        transaction_helpers=transaction_helpers,
        assets=assets,
    )
