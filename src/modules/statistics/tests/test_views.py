import pytest
from django.urls import reverse

from modules.investors.tests.conftest import create_fake_investor

pytestmark = pytest.mark.django_db


class TestStatisticsEndpoints:
    @pytest.fixture(autouse=True)
    def setup(self, user):
        self.investor = create_fake_investor(clerk_id=user.id, save=True)
        self.user = user

    def test_investor_stats_view_returns_200(self, api_client_auth):
        url = reverse("statistics:investor-stats")
        response = api_client_auth.get(url)

        assert response.status_code == 200
        assert set(response.data.keys()) == {
            "todays_gain",
            "total_gain",
            "invested",
            "total_value",
        }

    def test_current_account_value_view_returns_valid_fields(self, api_client_auth):
        url = reverse("statistics:current-account-value")
        response = api_client_auth.get(url)

        assert response.status_code == 200
        assert set(response.data.keys()) == {
            "total_account_value",
            "gain",
            "gain_percentage",
        }

    def test_asset_allocation_view_returns_valid_structure(self, api_client_auth):
        url = reverse("statistics:asset-allocation")
        response = api_client_auth.get(url)

        assert response.status_code == 200
        assert set(response.data.keys()) == {
            "total_value",
            "total_gain_this_year",
            "allocations",
        }
        assert isinstance(response.data["allocations"], list)

    def test_owned_shares_view_returns_list(self, api_client_auth):
        url = reverse("statistics:owned-shares")
        response = api_client_auth.get(url)

        assert response.status_code == 200
        assert isinstance(response.data, list)
        if response.data:
            item = response.data[0]
            assert "name" in item
            assert "symbol" in item
            assert "volume" in item
            assert "gain" in item

    def test_trading_overview_view_returns_expected_fields(self, api_client_auth):
        url = reverse("statistics:trading-overview")
        response = api_client_auth.get(url)

        assert response.status_code == 200
        assert set(response.data.keys()) == {
            "total_trades",
            "buys",
            "sells",
            "total_gain",
        }

    def test_most_traded_view_returns_list(self, api_client_auth):
        url = reverse("statistics:most-traded")
        response = api_client_auth.get(url)

        assert response.status_code == 200
        assert isinstance(response.data, list)
        if response.data:
            item = response.data[0]
            assert "symbol" in item
            assert "no_trades" in item
            assert "gain_percentage" in item

    def test_transaction_history_view_returns_positions(self, api_client_auth):
        url = reverse("statistics:transactions-history")
        response = api_client_auth.get(url)

        assert response.status_code == 200
        assert isinstance(response.data, list)
        if response.data:
            pos = response.data[0]
            assert "name" in pos
            assert "quantity" in pos
            assert "market_value" in pos
            assert "gain" in pos
            assert "history" in pos
