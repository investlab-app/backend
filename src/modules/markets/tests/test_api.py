import pytest
from django.urls import reverse

from modules.authentication.tests.conftest import user
from modules.core.tests.conftest import api_client, api_client_auth  # noqa: F401

pytestmark = pytest.mark.django_db


class TestMarketHolidaysListEndpoint:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.url = reverse("market-holidays")

    def test_happy(self, api_client_auth, mocker):
        fake_holidays = [
            {
                "date": "2025-12-25",
                "name": "Christmas Day",
                "status": "closed",
                "exchange": "NYSE",
                "open": None,
                "close": None,
            },
            {
                "date": "2025-01-01",
                "name": "New Year's Day",
                "status": "closed",
                "exchange": "NYSE",
                "open": None,
                "close": None,
            },
        ]
        mocker.patch(
            "modules.markets.repositories.PolygonMarketsRepository.list_market_holidays",
            return_value=fake_holidays,
        )

        response = api_client_auth.get(self.url)
        assert response.status_code == 200
        assert len(response.data) == 2
        assert response.data[0]["name"] == "Christmas Day"

    def test_no_auth(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 403

    def test_error_handling(self, api_client_auth, mocker):
        mocker.patch(
            "modules.markets.repositories.PolygonMarketsRepository.list_market_holidays",
            return_value=None,
        )
        response = api_client_auth.get(self.url)
        assert response.status_code == 500
        assert "Failed to fetch" in response.data


class TestMarketStatusEndpoint:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.url = reverse("market-status")

    def test_happy(self, api_client_auth, mocker):
        fake_status = {
            "market": "open",
            "server_time": "2025-09-12T12:00:00Z",
            "after_hours": False,
            "early_hours": False,
            "exchanges": {"nyse": "open"},
        }
        mocker.patch(
            "modules.markets.repositories.PolygonMarketsRepository.get_market_status",
            return_value=fake_status,
        )

        response = api_client_auth.get(self.url)
        assert response.status_code == 200
        assert response.data["market"] == "open"
        assert response.data["exchanges"]["nyse"] == "open"

    def test_no_auth(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 403

    def test_error_handling(self, api_client_auth, mocker):
        mocker.patch(
            "modules.markets.repositories.PolygonMarketsRepository.get_market_status",
            return_value=None,
        )
        response = api_client_auth.get(self.url)
        assert response.status_code == 500
        assert "Failed to fetch" in response.data
