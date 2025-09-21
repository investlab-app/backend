from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse

from modules.core.tests.conftest import api_client_auth  # noqa: F401
from modules.prices.schemas import PriceBar

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
        "start_date": "2025-01-01_00:00:00",
        "end_date": "2025-01-02_00:00:00",
        "interval": "DAY",
        "interval_multiplier": 2,
    }
    expected = [
        {
            "timestamp": "2025-01-01T00:00:00+01:00",
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
    assert response.status_code == 200
    assert response.data == expected
