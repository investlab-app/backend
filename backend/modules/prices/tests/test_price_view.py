from rest_framework.test import APIClient
from decimal import Decimal
from django.urls import reverse
from modules.users.models import User
from unittest.mock import patch
from datetime import datetime 
import pytest

@patch("modules.prices.views.PricesV2Service.get_ohlc")
def test_price_view(ohlc_mock):
    client = APIClient()
    user = User()
    client.force_authenticate(user)
    url = reverse('prices')

    ohlc_mock.return_value = [{
        'timestamp': datetime(2025, 1, 1, 0, 0, 0),
        'high': 5,
        'low': 1,
        'open': 1.5,
        'close': 2.4
    }]
    query_params = {
        'ticker': 'AAPL',
        'start_date': '2025-01-01_00:00:00',
        'end_date': '2025-01-02_00:00:00',
        'interval': 'DAY',
        'interval_multiplier': 2
    }
    expected = [{
        'timestamp': datetime(2025, 1, 1, 0, 0, 0),
        'high': Decimal('5'),
        'low': Decimal('1'),
        'open': Decimal('1.5'),
        'close': Decimal('2.4')
    }]


    response = client.get(url, data=query_params, format='json')
    response.data[0]['timestamp'] = response.data[0]['timestamp'].replace(tzinfo=None)
    assert response.data == expected
    assert response.status_code == 200
