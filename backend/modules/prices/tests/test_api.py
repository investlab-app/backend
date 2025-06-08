import pytest
from django.urls import reverse
from rest_framework.response import Response

from modules.core.tests.conftest import api_client_auth

pytestmark = pytest.mark.django_db


def test_prices_view_success(api_client_auth, mock_yfinance_repository) -> None:
    url = reverse("prices")
    response = api_client_auth.get(
        url,
        {
            "ticker": "aapl",
            "start_date": "2024-04-01T00:00:00",
            "end_date": "2024-04-30T00:00:00",
            "interval": "1d",
        },
    )
    assert isinstance(response, Response)
    assert response.status_code == 200

    response_data = response.json()
    assert isinstance(response_data, dict)
    assert "data" in response_data
    assert "min_price" in response_data
    assert "max_price" in response_data
    assert len(response_data["data"]) == 2
    assert response_data["min_price"] == 168.0
    assert response_data["max_price"] == 172.0


def test_missing_param_returns_400(api_client_auth, mock_yfinance_repository) -> None:
    url = reverse("prices")
    response = api_client_auth.get(url, {"ticker": "aapl"})
    assert isinstance(response, Response)
    assert response.status_code == 400


def test_startdate_gt_enddate(api_client_auth, mock_yfinance_repository) -> None:
    url = reverse("prices")
    response = api_client_auth.get(
        url,
        {
            "ticker": "aapl",
            "start_date": "2024-05-01T00:00:00",
            "end_date": "2024-04-30T00:00:00",
            "interval": "1d",
        },
    )
    assert isinstance(response, Response)
    assert response.status_code == 400


def test_invalid_interval(api_client_auth, mock_yfinance_repository) -> None:
    url = reverse("prices")
    response = api_client_auth.get(
        url,
        {
            "ticker": "aapl",
            "start_date": "2024-05-01T00:00:00",
            "end_date": "2024-04-30T00:00:00",
            "interval": "8d",
        },
    )
    assert isinstance(response, Response)
    assert response.status_code == 400
