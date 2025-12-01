from dataclasses import dataclass
from decimal import Decimal

import pytest
from pydantic import BaseModel, ConfigDict

from modules.investors.tests.conftest import create_fake_investor
from modules.instruments.tests.conftest import create_fake_instrument

from modules.core.constants import PrecisionType
from modules.instruments.models import Instrument
from modules.investors.models import Asset, Investor
from modules.transactions.models import Transaction, PartialTransaction
from modules.transactions.services import ExecutiveTransactionService, TransactionParams

pytestmark = pytest.mark.django_db


class TestSingleInvestorSingleInstrument:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.investor = create_fake_investor(balance=0, save=True)
        self.instrument = create_fake_instrument(save=True)

    def buy(self, volume: Decimal, action_price: Decimal):
        return ExecutiveTransactionService.buy(
            TransactionParams(
                investor=self.investor,
                instrument=self.instrument,
                volume=volume,
                price_per_unit=action_price,
            )
        )

    def sell(self, volume: Decimal, action_price: Decimal):
        return ExecutiveTransactionService.sell(
            TransactionParams(
                investor=self.investor,
                instrument=self.instrument,
                volume=volume,
                price_per_unit=action_price,
            )
        )

    def set_asset_volume(self, volume: Decimal):
        Asset.objects.create(
            investor=self.investor, ticker=self.instrument, volume=volume
        )

    def set_balance(self, balance: Decimal):
        self.investor.balance = balance
        self.investor.save()

    def get_asset(self):
        return Asset.objects.get(investor=self.investor, ticker=self.instrument)


class TestRegularTransactions(TestSingleInvestorSingleInstrument):
    def test_buy__not_enough_money__raises_value_error(self):
        self.set_balance(10)
        with pytest.raises(ValueError):
            self.buy(volume=15, action_price=1)

    def test_buy__enough_money__passes(self):
        self.set_balance(10)
        self.buy(volume=10, action_price=1)

    def test_buy__success__investor_balance_is_reduced(self):
        self.set_balance(10)
        self.buy(volume=3, action_price=2)
        assert self.investor.balance == 4

    def test_buy__no_asset_in_db__asset_is_created(self):
        self.set_balance(10)
        self.buy(volume=5, action_price=2)

        asset = self.get_asset()
        assert asset.investor == self.investor
        assert asset.ticker == self.instrument
        assert asset.volume == 5

    def test_buy__asset_in_db__asset_volume_grows(self):
        self.set_asset_volume(5)
        self.set_balance(10)

        self.buy(volume=2, action_price=3)

        self.get_asset().volume == 7

    def test_buy__transaction_is_saved(self):
        self.set_balance(10)
        self.buy(volume=10, action_price=1)

        assert len(Transaction.objects.all()) == 1
        transaction = Transaction.objects.first()

        assert transaction.investor == self.investor
        assert transaction.ticker == self.instrument
        assert transaction.volume == 10
        assert transaction.price == 1
        assert transaction.is_buy == True

    def test_sell__no_assets_in_db__raises_value_error(self):
        with pytest.raises(ValueError):
            self.sell(volume=1, action_price=1)

    def test_sell__enough_assets__passes(self):
        self.set_balance(10)
        self.buy(volume=1, action_price=1)
        self.sell(volume=1, action_price=1)

    def test_sell__not_enough_assets__raises_value_error(self):
        self.set_balance(10)
        self.buy(volume=1, action_price=1)
        with pytest.raises(ValueError):
            self.sell(volume=2, action_price=1)

    def test_sell__success__balance_is_added(self):
        self.set_balance(10)
        self.buy(volume=10, action_price=1)
        self.set_balance(2)
        self.sell(volume=2, action_price=3)

        assert self.investor.balance == 8

    def test_sell__success__assets_volume_is_reduced(self):
        self.set_balance(10)
        self.buy(volume=10, action_price=1)
        self.sell(volume=2, action_price=6)

        assert self.get_asset().volume == 8

    def test_sell__asset_volume_gets_to_zero__asset_is_removed(self):
        self.set_balance(10)
        self.buy(volume=10, action_price=1)
        self.sell(10, 1)

        with pytest.raises(Exception):
            self.get_asset()

    def test_sell__success__transaction_is_created(self):
        self.set_balance(10)
        self.buy(volume=10, action_price=1)
        self.sell(volume=10, action_price=1)

        assert len(Transaction.objects.all()) == 2
        transaction = Transaction.objects.first()

        assert transaction.investor == self.investor
        assert transaction.ticker == self.instrument
        assert transaction.volume == 10
        assert transaction.price == 1
        assert transaction.is_buy == False

    # test_sell__volume_zero__raises_value_error(self):
    # test_buy__volume_zero__raises_value_error(self):
    # test_buy__negative_price__raises_value_error(self):
    # test_sell__negative_price__raises_value_error(self):


class PartialData(BaseModel):
    buy: Transaction
    sell: Transaction | None
    volume: Decimal

    class Config:
        arbitrary_types_allowed = True

    def __hash__(self):
        return hash(self.buy.id)


class TestPartialTransactions(TestSingleInvestorSingleInstrument):
    def partial_transaction_exists(self, partial: PartialData) -> bool:
        try:
            PartialTransaction.objects.get(
                buy_transaction=partial.buy,
                sell_transaction=partial.sell,
                volume=Decimal(partial.volume),
            )
            return True
        except:
            return False

    def partial_transactions_equal(self, partial: list[PartialData]) -> bool:
        if not len(partial) == len(PartialTransaction.objects.all()):
            return False

        for p in partial:
            if not self.partial_transaction_exists(p):
                return False
        return True

    def get_partial_transaction_data(self) -> list[PartialData]:
        data = set()
        for partial in PartialTransaction.objects.all():
            data.add(
                PartialData(
                    buy=partial.buy_transaction,
                    sell=partial.sell_transaction,
                    volume=partial.volume,
                )
            )
        return data

    def test_buy__success__partial_transaction_without_sell_is_created(self):
        self.set_balance(10)
        buy = self.buy(volume=10, action_price=1)

        expected = set([PartialData(buy=buy, sell=None, volume=10)])
        assert self.get_partial_transaction_data() == expected

    def test_sell__success__partial_transaction_is_created(self):
        self.set_balance(10)
        buy = self.buy(volume=10, action_price=1)
        sell = self.sell(volume=10, action_price=1)

        expected = set([PartialData(buy=buy, sell=sell, volume=10)])
        assert self.get_partial_transaction_data() == expected

    def test_sell_partial_asset__partial_transaction_gets_split(self):
        self.set_balance(100)
        buy = self.buy(volume=10, action_price=1)
        sell = self.sell(volume=3, action_price=1)

        expected = set(
            [
                PartialData(buy=buy, sell=sell, volume=3),
                PartialData(buy=buy, sell=None, volume=7),
            ]
        )
        assert self.get_partial_transaction_data() == expected

    def test_sell_partial_asset_twice__asset_is_completely_sold(self):
        self.set_balance(100)
        buy = self.buy(volume=10, action_price=1)
        sell_1 = self.sell(volume=4, action_price=1)
        sell_2 = self.sell(volume=6, action_price=1)

        expected = set(
            [
                PartialData(buy=buy, sell=sell_1, volume=4),
                PartialData(buy=buy, sell=sell_2, volume=6),
            ]
        )
        assert self.get_partial_transaction_data() == expected

    def test_sell_partial_asset_twice__asset_is_partially_sold(self):
        self.set_balance(100)
        buy = self.buy(volume=10, action_price=1)
        sell_1 = self.sell(volume=2, action_price=1)
        sell_2 = self.sell(volume=3, action_price=1)

        expected = set(
            [
                PartialData(buy=buy, sell=sell_1, volume=2),
                PartialData(buy=buy, sell=sell_2, volume=3),
                PartialData(buy=buy, sell=None, volume=5),
            ]
        )
        assert self.get_partial_transaction_data() == expected

    def test_multiple_buys__multiple_partials_get_created(self):
        self.set_balance(100)
        buy_1 = self.buy(volume=10, action_price=1)
        buy_2 = self.buy(volume=5, action_price=1)
        buy_3 = self.buy(volume=15, action_price=1)

        expected = set(
            [
                PartialData(buy=buy_1, sell=None, volume=10),
                PartialData(buy=buy_2, sell=None, volume=5),
                PartialData(buy=buy_3, sell=None, volume=15),
            ]
        )
        assert self.get_partial_transaction_data() == expected

    # def test_sell_covers_multiple_buys(self):
    #     self.set_balance(100)
    #     buy_1 = self.buy(volume=10, action_price=1)
    #     buy_2 = self.buy(volume=5, action_price=1)
    #     sell_1 = self.sell(volume=13, action_price=1)

    #     expected = set(
    #         [
    #             PartialData(buy=buy_1, sell=sell_1, volume=10),
    #             PartialData(buy=buy_2, sell=sell_1, volume=3),
    #             PartialData(buy=buy_2, sell=None, volume=2),
    #         ]
    #     )
    #     assert self.get_partial_transaction_data() == expected
