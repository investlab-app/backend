import pytest
from dependency_injector import containers, providers
from django.urls import reverse
from rest_framework.response import Response

from config import container
from modules.core.tests.conftest import api_client_auth
from modules.instruments.tests.conftest import mock_yfinance_repository
from modules.users.tests.conftest import user

pytestmark = pytest.mark.django_db


def test_instruments_available_view_success(
    api_client_auth, mock_yfinance_repository
) -> None:
    url = reverse("instruments-available")
    with container.instruments_container.instruments_repository.override(
        mock_yfinance_repository
    ):
        response = api_client_auth.get(url)
    assert isinstance(response, Response)
    assert response.status_code == 200
    assert isinstance(response.data, dict)
    assert "instruments" in response.data
    assert isinstance(response.data["instruments"], list)
    assert len(response.data["instruments"]) > 0


def test_instruments_list_view_success(
    api_client_auth, mock_yfinance_repository
) -> None:
    url = reverse("instruments-list")
    with container.instruments_container.instruments_repository.override(
        mock_yfinance_repository
    ):
        response = api_client_auth.get(
            url,
            {
                "tickers": "AAPL,MSFT",
                "page": 1,
                "page_size": 10,
                "sort_by": "market_cap",
                "sort_direction": "desc",
            },
        )
    assert isinstance(response, Response)
    assert response.status_code == 200
    assert isinstance(response.data, dict)
    assert "items" in response.data
    assert "total" in response.data
    assert "page" in response.data
    assert "page_size" in response.data
    assert "num_pages" in response.data
    assert len(response.data["items"]) > 0


def test_instrument_detail_view_success(
    api_client_auth, mock_yfinance_repository
) -> None:
    url = reverse("instrument-detail", kwargs={"ticker": "AAPL"})
    with container.instruments_container.instruments_repository.override(
        mock_yfinance_repository
    ):
        response = api_client_auth.get(url)
    assert isinstance(response, Response)
    assert response.status_code == 200
    assert isinstance(response.data, dict)
    assert "ticker" in response.data
    assert "name" in response.data
    assert "current_price" in response.data
    assert "market_cap" in response.data


def test_instrument_detail_view_invalid_ticker(api_client_auth) -> None:
    url = reverse("instrument-detail", kwargs={"ticker": "INVALID"})
    response = api_client_auth.get(url)
    assert isinstance(response, Response)
    assert response.status_code == 400


def test_instrument_news_view_success(
    api_client_auth, mock_yfinance_repository
) -> None:
    url = reverse("instrument-news", kwargs={"ticker": "AAPL"})
    with container.instruments_container.instruments_repository.override(
        mock_yfinance_repository
    ):
        response = api_client_auth.get(url)
    assert isinstance(response, Response)
    assert response.status_code == 200
    assert isinstance(response.data, list)
    assert len(response.data) > 0
    assert all(isinstance(item, dict) for item in response.data)


def test_instrument_news_view_invalid_ticker(api_client_auth) -> None:
    url = reverse("instrument-news", kwargs={"ticker": "INVALID"})
    response = api_client_auth.get(url)
    assert isinstance(response, Response)
    assert response.status_code == 400
