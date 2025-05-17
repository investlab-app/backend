import pytest

from rest_framework.test import APIClient
from django.urls import reverse
from rest_framework.response import Response

from modules.users.tests.conftest import user
from modules.core.tests.conftest import api_client_auth
from modules.prices.tests.conftest import mock_yfinance_repository


pytestmark = pytest.mark.django_db

def test_prices_view_success(api_client_auth, mock_yfinance_repository) -> None:
    url = reverse('prices') 
    response = api_client_auth.get(url, {
        "ticker": "aapl",
        "start_date": "2024-04-01T00:00:00",
        "end_date": "2024-04-30T00:00:00",
        "interval": "1d"
    })
    assert isinstance(response, Response)
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_missing_param_returns_400(api_client_auth, mock_yfinance_repository) -> None:
    url = reverse('prices')
    response = api_client_auth.get(url, {"ticker": "aapl"})  
    assert isinstance(response, Response)
    assert response.status_code == 400

def test_startdate_gt_enddate(api_client_auth, mock_yfinance_repository) -> None:
    url = reverse('prices') 
    response = api_client_auth.get(url, {
        "ticker": "aapl",
        "start_date": "2024-05-01T00:00:00",
        "end_date": "2024-04-30T00:00:00",
        "interval": "1d"
    })
    assert isinstance(response, Response)
    assert response.status_code == 400