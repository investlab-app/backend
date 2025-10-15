from decimal import Decimal

import faker
import pytest

from modules.investors.models import AccountValueSnapshot, Investor
from modules.investors.services import InvestorStatsService, InvestorValueHistoryService
from modules.investors.tests.test_investor_stats_service import investor_factory

fake = faker.Faker()
pytestmark = pytest.mark.django_db


class TestInvestorValueHistoryService:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        self.stats_service_mock = mocker.Mock(spec=InvestorStatsService)
        self.service = InvestorValueHistoryService(
            stats_service=self.stats_service_mock
        )

    def test_save_all_investors__no_investors__creates_no_snapshots(self):
        assert Investor.objects.count() == 0

        self.service.save_all_investors()

        assert AccountValueSnapshot.objects.count() == 0

    def test_save_all_investors__multiple_investors__creates_snapshots_for_all(
        self, investor_factory
    ):
        investor1 = investor_factory()
        investor2 = investor_factory()

        def side_effect(investor):
            if investor == investor1:
                return Decimal(350)
            if investor == investor2:
                return Decimal(200)
            return Decimal(0)

        self.stats_service_mock.get_total_value.side_effect = side_effect

        self.service.save_all_investors()

        assert AccountValueSnapshot.objects.count() == 2
        snapshot1 = AccountValueSnapshot.objects.get(investor=investor1)
        snapshot2 = AccountValueSnapshot.objects.get(investor=investor2)
        assert snapshot1.value == Decimal(350)
        assert snapshot2.value == Decimal(200)
