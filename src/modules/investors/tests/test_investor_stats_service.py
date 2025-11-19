from collections import defaultdict
from decimal import Decimal

import pytest

from modules.investors.models import Asset, Investor
from modules.investors.services import InvestorStatsService
from modules.investors.tests.conftest import asset_factory, investor_factory
from modules.prices.tests.conftest import PriceRepositoryMock

pytestmark = pytest.mark.django_db


class LatestPriceServiceMock(PriceRepositoryMock):
    def __init__(self, investor: Investor):
        super().__init__()
        self.investor = investor

    def get_prices_default_dict(
        self, factory=lambda: Decimal(1)
    ) -> defaultdict[str, Decimal]:
        assets = Asset.objects.filter(investor=self.investor)
        tickers = [a.ticker.ticker.upper() for a in assets]
        price_bars = self.get_prices_map(tickers)
        data = {ticker: price.current_price for ticker, price in price_bars.items()}
        prices_dict = defaultdict(factory)
        prices_dict.update(data)
        return prices_dict


class TestInvestorStats:
    @pytest.fixture(autouse=True)
    def setup(self, investor_factory):
        self.investor = investor_factory(balance=0)
        self.mock = LatestPriceServiceMock(investor=self.investor)
        self.service = InvestorStatsService(price_service=self.mock)

    @pytest.mark.parametrize("balance", [0, 10])
    def test_get_total_value__no_assets__returns_balance(self, balance):
        self.investor.balance = balance
        self.investor.save()

        value = self.service.get_total_value(self.investor)

        assert value == balance

    def test_get_total_value__multiple_assets_returns_valid_value(self, asset_factory):
        self.investor.balance = 10
        self.investor.save()
        asset1 = asset_factory(investor=self.investor, volume=5)
        asset2 = asset_factory(investor=self.investor, volume=10)
        self.mock.set_price(asset1.ticker, price=15)
        self.mock.set_price(asset2.ticker, price=30)

        value = self.service.get_total_value(self.investor)

        assert value == 10 + 5 * 15 + 10 * 30

    def test_get_total_value__other_investors_get_ignored(
        self, investor_factory, asset_factory
    ):
        impostor = investor_factory(balance=2)
        good_assets = [
            asset_factory(investor=self.investor, volume=1) for _ in range(4)
        ]
        bad_assets = [asset_factory(investor=impostor) for _ in range(3)]
        [self.mock.set_price(a.ticker, 1) for a in good_assets]

        value = self.service.get_total_value(self.investor)

        assert value == 4

    def test_asset_allocation__no_assets__returns_empty_list(self):
        assert self.service.get_asset_allocation(self.investor) == []

    def test_asset_allocation__single_asset__returns_valid_asset_allocation(
        self, asset_factory
    ):
        asset = asset_factory(investor=self.investor, volume=5)
        self.mock.set_price(asset.ticker, price=10)

        allocation = self.service.get_asset_allocation(self.investor)[0]

        assert allocation.percentage == 100
        assert allocation.asset == asset
        assert allocation.price_per_action == 10
        assert allocation.total_value == 5 * 10

    def test_asset_allocation__multiple_assets__valid_percentages(self, asset_factory):
        asset1 = asset_factory(investor=self.investor, volume=5)
        asset2 = asset_factory(investor=self.investor, volume=10)
        self.mock.set_price(asset1.ticker, 2)
        self.mock.set_price(asset2.ticker, 5)

        allocations = self.service.get_asset_allocation(self.investor)

        a_1 = list(filter(lambda x: x.asset == asset1, allocations))[0]
        a_2 = list(filter(lambda x: x.asset == asset2, allocations))[0]

        assert round(a_1.percentage, 3) == round((5 * 2) / (5 * 2 + 10 * 5) * 100, 3)
        assert round(a_2.percentage, 3) == round((10 * 5) / (5 * 2 + 10 * 5) * 100, 3)

    def test_asset_allocation__ignores_other_investors_assets(
        self, investor_factory, asset_factory
    ):
        impostor = investor_factory()
        good_assets = [
            asset_factory(investor=self.investor, volume=1) for _ in range(4)
        ]
        bad_assets = [asset_factory(investor=impostor) for _ in range(3)]
        [self.mock.set_price(a.ticker, 1) for a in good_assets]

        allocations = self.service.get_asset_allocation(self.investor)

        assert len(allocations) == 4
