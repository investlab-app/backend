from decimal import Decimal

import pytest

from modules.instruments.tests.conftest import instruments_factory
from modules.investors.models import Asset, Investor
from modules.transactions.models import Transaction
from modules.transactions.schemas import TransactionParams
from modules.transactions.services import ExecuteTransactionService

pytestmark = pytest.mark.django_db


class TestCase:
    @pytest.fixture(autouse=True)
    def setup(self, instruments_factory):
        self.investor = Investor.objects.create(clerk_id="asdf", balance=0)
        self.ticker = instruments_factory()
        self.service = ExecuteTransactionService()

    def _run_simple_buy_test_case(
        self,
        balance=Decimal(10),
        action_price=Decimal("2.5"),
        volume=Decimal(2),
    ):
        self.investor.balance = balance
        self.investor.save()
        self.action_price = action_price
        self.volume = volume

        params = TransactionParams(
            investor=self.investor,
            ticker=self.ticker,
            volume=self.volume,
            action_price=self.action_price,
        )
        self.service.buy(params)

    def _run_simple_sell_test_case(
        self,
        balance=Decimal(10),
        action_price=Decimal("2.5"),
        volume=Decimal(2),
    ):
        self.investor.balance = balance
        self.investor.save()
        self.action_price = action_price
        self.volume = volume

        params = TransactionParams(
            investor=self.investor,
            ticker=self.ticker,
            volume=self.volume,
            action_price=self.action_price,
        )
        self.service.sell(params)

    def test_buy__enough_money__transaction_gets_created(self):
        self._run_simple_buy_test_case()

        assert Transaction.objects.count() == 1
        transaction: Transaction = (  # ty: ignore[invalid-assignment]
            Transaction.objects.first()
        )

        assert transaction.investor == self.investor
        assert transaction.ticker == self.ticker
        assert transaction.volume == self.volume
        assert transaction.price == self.volume * self.action_price
        assert transaction.is_buy is True

    def test_buy__not_enough_money__exception_gets_raised(self):
        with pytest.raises(ValueError):
            self._run_simple_buy_test_case(
                balance=Decimal(0),
            )

    def test_buy__success__balance_is_updated(self):
        self._run_simple_buy_test_case()

        self.investor.refresh_from_db()
        assert self.investor.balance == Decimal(5)

    def test_buy__asset_does_not_exist__assets_gets_created(self):
        self._run_simple_buy_test_case()

        assert Asset.objects.count() == 1
        asset: Asset = Asset.objects.first()  # ty: ignore[invalid-assignment]
        assert asset.investor == self.investor
        assert asset.volume == self.volume
        assert asset.ticker == self.ticker

    def test_buy__asset_exists__assets_gets_updated(self):
        initial_volume = Decimal(5)
        asset: Asset = Asset.objects.create(  # ty: ignore[invalid-assignment]
            investor=self.investor,
            ticker=self.ticker,
            volume=initial_volume,
        )

        self._run_simple_buy_test_case()

        assert Asset.objects.count() == 1
        asset.refresh_from_db()
        assert asset.volume == initial_volume + self.volume

    def test_sell__success__transaction_gets_created(self):
        Asset.objects.create(
            investor=self.investor, ticker=self.ticker, volume=Decimal(10)
        )
        self._run_simple_sell_test_case()

        assert Transaction.objects.count() == 1
        transaction: Transaction = (  # ty: ignore[invalid-assignment]
            Transaction.objects.first()
        )

        assert transaction.investor == self.investor
        assert transaction.ticker == self.ticker
        assert transaction.volume == self.volume
        assert transaction.price == self.volume * self.action_price
        assert transaction.is_buy is False

    def test_sell__success__asset_gets_updated(self):
        initial_volume = Decimal(10)
        asset: Asset = Asset.objects.create(  # ty: ignore[invalid-assignment]
            investor=self.investor,
            ticker=self.ticker,
            volume=initial_volume,
        )

        self._run_simple_sell_test_case()

        asset.refresh_from_db()
        assert asset.volume == initial_volume - self.volume

    def test_sell__enough_assets__balance_is_updated(self):
        initial_balance = Decimal(100)
        Asset.objects.create(
            investor=self.investor, ticker=self.ticker, volume=Decimal(10)
        )

        self._run_simple_sell_test_case(balance=initial_balance)

        self.investor.refresh_from_db()
        transaction_value = self.volume * self.action_price
        assert self.investor.balance == initial_balance + transaction_value

    def test_sell__not_enough_assets__exception_gets_raised(self):
        Asset.objects.create(
            investor=self.investor, ticker=self.ticker, volume=Decimal(1)
        )

        with pytest.raises(ValueError):
            self._run_simple_sell_test_case(volume=Decimal(2))
