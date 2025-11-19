from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from modules.investors.tests.conftest import (
    asset_factory,
)
from modules.orders.services.order_services import OrderFailureReason, OrderService
from modules.orders.tests.conftest import fake_limit_order, fake_market_order
from modules.prices.tests.conftest import get_fake_price_bar

pytestmark = pytest.mark.django_db


# Missing tests
# - Is the order actually saved to the db
# - Is blocked_funds correctly updated
# - Entire delete function
class TestOrderService:
    @pytest.fixture(autouse=True)
    def setup(self, asset_factory):
        self.latest_price_service_mock = MagicMock()
        self.order_service = OrderService(self.latest_price_service_mock)
        self.asset = asset_factory(volume=Decimal(5))
        self.investor = self.asset.investor
        self.instrument = self.asset.ticker

    def market_order(self, *, is_buy: bool, volume: Decimal):
        fake_market_order(
            investor=self.investor,
            ticker=self.instrument,
            is_buy=is_buy,
            volume=Decimal(volume),
            save=True,
        )

    def limit_order(self, *, is_buy: bool, volume: Decimal, limit_price: Decimal):
        fake_limit_order(
            investor=self.investor,
            ticker=self.instrument,
            is_buy=is_buy,
            volume=Decimal(volume),
            limit_price=Decimal(limit_price),
            save=True,
        )

    def order_service_create_market(self, *, is_buy: bool, volume: Decimal):
        return self.order_service.create_market(
            investor=self.investor,
            instrument=self.instrument,
            volume=Decimal(volume),
            is_buy=is_buy,
        )

    def order_service_create_limit(
        self, *, is_buy: bool, volume: Decimal, limit_price: Decimal
    ):
        return self.order_service.create_limit(
            investor=self.investor,
            instrument=self.instrument,
            volume=Decimal(volume),
            is_buy=is_buy,
            limit_price=Decimal(limit_price),
        )

    def set_asset_volume(self, volume: Decimal):
        self.asset.volume = volume
        self.asset.save()

    def set_blocked_funds(self, blocked_funds: Decimal):
        self.investor.blocked_funds = Decimal(blocked_funds)
        self.investor.save()

    def set_asset_price(self, price):
        if price is None:
            fake_prices = {}
        else:
            fake_prices = {self.asset.ticker.ticker: get_fake_price_bar(close=price)}
        self.latest_price_service_mock.get_prices.return_value = fake_prices

    def set_investor_balance(self, balance):
        self.investor.balance = balance
        self.investor.save()

    def test__create_market_sell__enough_assets__passes(self):
        self.set_asset_volume(volume=5)

        order, _err = self.order_service_create_market(is_buy=False, volume=3)

        assert order is not None

    def test__create_market_sell__not_enough_assets__fails(self):
        self.set_asset_volume(volume=5)

        order, err = self.order_service_create_market(is_buy=False, volume=6)

        assert order is None
        assert err == OrderFailureReason.ASSETS

    def test__create_market_sell__some_assets_blocked__passes(self):
        self.set_asset_volume(volume=10)
        self.market_order(is_buy=False, volume=5)

        order, _err = self.order_service_create_market(is_buy=False, volume=5)

        assert order is not None

    def test__create_market_sell__too_many_assets_blocked__fails(self):
        self.set_asset_volume(volume=10)
        self.market_order(is_buy=False, volume=5)

        order, err = self.order_service_create_market(is_buy=False, volume=6)

        assert order is None
        assert err == OrderFailureReason.ASSETS

    def test__create_market_sell__respects_blocked_assets_from_other_orders(self):
        self.set_asset_volume(volume=10)
        self.limit_order(is_buy=False, volume=10, limit_price=0)

        order, err = self.order_service_create_market(is_buy=False, volume=1)

        assert order is None
        assert err == OrderFailureReason.ASSETS

    def test__create_market_buy__enough_funds__passes(self):
        self.set_asset_price(price=1)
        self.set_investor_balance(5)

        order, _err = self.order_service_create_market(is_buy=True, volume=5)

        assert order is not None

    def test__create_market_buy__price_is_missing__fails(self):
        self.set_asset_price(None)
        self.set_investor_balance(5)

        order, err = self.order_service_create_market(is_buy=True, volume=5)

        assert order is None
        assert err == OrderFailureReason.UNKNOWN

    def test__create_market_buy__not_enough_funds__fails(self):
        self.set_asset_price(price=1)
        self.set_investor_balance(5)

        order, err = self.order_service_create_market(is_buy=True, volume=10)

        assert order is None
        assert err == OrderFailureReason.FUNDS

    def test__create_market_buy__funds_partially_blocked__passes(self):
        self.set_asset_price(1)
        self.set_investor_balance(10)
        self.set_blocked_funds(5)

        order, _err = self.order_service_create_market(is_buy=True, volume=5)

        assert order is not None

    def test__create_market_buy__funds_partially_blocked__fails(self):
        self.set_asset_price(1)
        self.set_investor_balance(10)
        self.set_blocked_funds(10)

        order, err = self.order_service_create_market(is_buy=True, volume=6)

        assert order is None
        assert err == OrderFailureReason.FUNDS

    def test__create_limit_buy__enough_money__passes(self):
        self.set_investor_balance(10)
        self.set_blocked_funds(5)

        order, _err = self.order_service_create_limit(
            is_buy=True, volume=5, limit_price=1
        )

        assert order is not None

    def test__create_limit_buy__not_enough_money__fails(self):
        self.set_investor_balance(10)
        self.set_blocked_funds(5)

        order, err = self.order_service_create_limit(
            is_buy=True, volume=6, limit_price=1
        )

        assert order is None
        assert err == OrderFailureReason.FUNDS

    def test_create_limit_sell_respects_blocked_from_other_orders(self):
        self.asset.volume = 10
        self.asset.save()

        self.market_order(is_buy=False, volume=5)
        self.market_order(is_buy=False, volume=3)

        order, err1 = self.order_service_create_limit(
            volume=Decimal(3),
            is_buy=False,
            limit_price=Decimal(1),
        )
        order2, _err2 = self.order_service_create_limit(
            volume=Decimal(2),
            is_buy=False,
            limit_price=Decimal(1),
        )

        assert order is None
        assert err1 == OrderFailureReason.ASSETS
        assert order2 is not None
