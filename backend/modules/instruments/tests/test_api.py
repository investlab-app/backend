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


def test_instruments_list_view_success(api_client_auth, mock_yfinance_repository) -> None:
    url = reverse("instruments-list")
    response = api_client_auth.get(
        url,
        {
            "tickers": "aapl,msft,goog",
            "page": "1",
            "page_size": "10",
        },
    )
    assert isinstance(response, Response)
    assert response.status_code == 200

    response_data = response.json()
    assert isinstance(response_data, dict)
    assert "items" in response_data
    assert "total" in response_data
    assert "page" in response_data
    assert "page_size" in response_data
    assert "num_pages" in response_data
    assert len(response_data["items"]) == 2
    assert response_data["total"] == 2
    assert response_data["items"][0]["ticker"] == "AAPL"


def test_instruments_missing_param_returns_400(api_client_auth) -> None:
    url = reverse("instruments-list")
    response = api_client_auth.get(url)
    assert isinstance(response, Response)
    assert response.status_code == 400


def test_instrument_detail_view_success(api_client_auth, mock_yfinance_repository) -> None:
    url = reverse("instrument-detail", kwargs={"ticker": "aapl"})
    response = api_client_auth.get(url)
    assert isinstance(response, Response)
    assert response.status_code == 200
    
    response_data = response.json()
    assert isinstance(response_data, dict)
    assert response_data["ticker"] == "AAPL"
    assert response_data["name"] == "Apple Inc."
    assert "business_summary" in response_data
