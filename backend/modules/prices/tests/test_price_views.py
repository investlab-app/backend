from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse

from modules.core.tests.conftest import api_client_auth
from modules.prices.schemas import PriceBar, PriceDaily, PriceDailySummary

pytestmark = pytest.mark.django_db


@patch("modules.prices.views.PolygonPricesRepository.get_ohlc")
def test_price_bar_view(ohlc_mock, api_client_auth):
    url = reverse("prices-bars")

    ohlc_mock.return_value = [
        PriceBar(
            timestamp=datetime(2025, 1, 1, 0, 0, 0),
            open=Decimal("100.50"),
            high=Decimal("110.00"),
            low=Decimal("95.25"),
            close=Decimal("105.75"),
            volume=Decimal("12345.67"),
            transactions=42,
            volume_weighted_average_price=Decimal("103.12"),
        )
    ]
    query_params = {
        "ticker": "AAPL",
        "start_date": "2025-01-01T00:00:00Z",
        "end_date": "2025-01-02T00:00:00Z",
        "interval": "DAY",
        "interval_multiplier": 2,
    }
    expected = [
        {
            "timestamp": "2025-01-01T00:00:00",
            "open": "100.50",
            "high": "110.00",
            "low": "95.25",
            "close": "105.75",
            "volume": "12345.67",
            "transactions": 42,
            "volume_weighted_average_price": "103.12",
        }
    ]

    response = api_client_auth.get(url, data=query_params)
    response.data[0]["timestamp"] = response.data[0]["timestamp"].split("+")[0]
    assert response.status_code == 200
    assert response.data == expected


@patch("modules.prices.views.PolygonPricesRepository.get_prices")
def test_price_list_view(get_prices_mock, api_client_auth):
    url = reverse("prices-list")

    get_prices_mock.return_value = [
        PriceDailySummary(
            ticker="AAPL",
            current_price=Decimal("150.25"),
            daily_summary=PriceDaily(
                open=Decimal("149.50"),
                high=Decimal("151.00"),
                low=Decimal("148.75"),
                close=Decimal("150.25"),
                volume=Decimal(1234567),
                volume_weighted_average_price=Decimal("150.10"),
            ),
            todays_change=Decimal("0.75"),
            todays_change_percent=Decimal("0.50"),
            last_updated=datetime(2025, 9, 21, 12, 0),
        )
    ]

    query_params = {"tickers": ["AAPL"]}

    expected = [
        {
            "ticker": "AAPL",
            "current_price": "150.25",
            "daily_summary": {
                "open": "149.50",
                "high": "151.00",
                "low": "148.75",
                "close": "150.25",
                "volume": "1234567.00",
                "volume_weighted_average_price": "150.10",
            },
            "todays_change": "0.75",
            "todays_change_percent": "0.50",
            "last_updated": "2025-09-21T12:00:00",
        }
    ]

    response = api_client_auth.get(url, data=query_params)
    response.data[0]["last_updated"] = response.data[0]["last_updated"].split("+")[0]
    assert response.status_code == 200
    assert response.data == expected


@patch("modules.prices.views.PolygonPricesRepository.get_price")
def test_price_retrieve_view(get_price_mock, api_client_auth):
    url = reverse("prices-detail", args=["AAPL"])

    get_price_mock.return_value = PriceDailySummary(
        ticker="AAPL",
        current_price=Decimal("150.25"),
        daily_summary=PriceDaily(
            open=Decimal("149.50"),
            high=Decimal("151.00"),
            low=Decimal("148.75"),
            close=Decimal("150.25"),
            volume=Decimal(1234567),
            volume_weighted_average_price=Decimal("150.10"),
        ),
        todays_change=Decimal("0.75"),
        todays_change_percent=Decimal("0.50"),
        last_updated=datetime(2025, 9, 21, 12, 0),
    )

    expected = {
        "ticker": "AAPL",
        "current_price": "150.25",
        "daily_summary": {
            "open": "149.50",
            "high": "151.00",
            "low": "148.75",
            "close": "150.25",
            "volume": "1234567.00",
            "volume_weighted_average_price": "150.10",
        },
        "todays_change": "0.75",
        "todays_change_percent": "0.50",
        "last_updated": "2025-09-21T12:00:00",
    }

    response = api_client_auth.get(url)
    response.data["last_updated"] = response.data["last_updated"].split("+")[0]
    assert response.status_code == 200
    assert response.data == expected
