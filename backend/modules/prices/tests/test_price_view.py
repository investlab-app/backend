from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

from django.urls import reverse

from modules.core.tests.conftest import api_client_auth  # noqa: F401

pytestmark = pytest.mark.django_db


@patch("modules.prices.views.PricesV2Service.get_ohlc")
def test_price_view(ohlc_mock, api_client_auth):
    url = reverse("prices")

    ohlc_mock.return_value = [
        {
            "timestamp": datetime(2025, 1, 1, 0, 0, 0),
            "high": 5,
            "low": 1,
            "open": 1.5,
            "close": 2.4,
        }
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
            "timestamp": datetime(2025, 1, 1, 0, 0, 0),
            "high": Decimal("5"),
            "low": Decimal("1"),
            "open": Decimal("1.5"),
            "close": Decimal("2.4"),
        }
    ]

    response = api_client_auth.get(url, data=query_params, format="json")
    response.data[0]["timestamp"] = response.data[0]["timestamp"].replace(tzinfo=None)
    assert response.data == expected
    assert response.status_code == 200
