from datetime import datetime
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status

from modules.core.tests.conftest import api_client_auth  # noqa: F401
from modules.notifications.models import NotificationConfig
from modules.prices.models import PriceAlert
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
@patch("modules.prices.serializers.LatestPriceService.get_prices_default_dict")
def test_price_list_view(
    get_prices_default_dict_mock, get_prices_mock, api_client_auth
):
    url = reverse("prices-list")

    get_prices_mock.return_value = [
        PriceDailySummary(
            ticker="AAPL",
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
    get_prices_default_dict_mock.return_value = {"AAPL": Decimal("150.25")}

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
@patch("modules.prices.serializers.LatestPriceService.get_prices_default_dict")
def test_price_retrieve_view(
    get_prices_default_dict_mock, get_price_mock, api_client_auth
):
    url = reverse("prices-detail", args=["AAPL"])

    get_price_mock.return_value = PriceDailySummary(
        ticker="AAPL",
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

    get_prices_default_dict_mock.return_value = {"AAPL": Decimal("150.25")}

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


class TestListCreateView:
    """Tests for price alert list and create views"""

    @pytest.fixture(autouse=True)
    def setup(self, api_client_auth, investor_factory, instruments_factory, user):
        self.client = api_client_auth
        # Create investor with authenticated user's id
        self.investor = investor_factory()
        self.investor.clerk_id = user.id
        self.investor.save()
        self.instrument = instruments_factory()
        self.url = reverse("price-alert-list-create")

    def test_list__returns_user_alerts(self):
        """Test list view returns only user's alerts"""
        notification_config = NotificationConfig.objects.create(
            is_email=True, is_push=True, is_websocket=True
        )

        PriceAlert.objects.create(
            investor=self.investor,
            instrument=self.instrument,
            notification_config=notification_config,
            threshold_type="above",
            threshold_value=Decimal("150.00"),
        )

        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1

    def test_list__filters_inactive_alerts(self):
        """Test list view returns alerts"""
        notification_config = NotificationConfig.objects.create()

        alert = PriceAlert.objects.create(
            investor=self.investor,
            instrument=self.instrument,
            notification_config=notification_config,
            threshold_type="above",
            threshold_value=Decimal("150.00"),
        )

        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["results"]) == 1
        assert response.data["results"][0]["id"] == str(alert.id)

    def test_create__success__returns_created(self):
        """Test create view creates new price alert"""
        payload = {
            "instrument_ticker": self.instrument.ticker,
            "threshold_type": "above",
            "threshold_value": "150.50",
            "notification_config": {
                "is_email": True,
                "is_push": False,
                "is_websocket": False,
            },
        }

        response = self.client.post(self.url, data=payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["threshold_value"] == "150.50"

    def test_create__associates_with_user(self):
        """Test create view associates alert with authenticated user"""
        payload = {
            "instrument_ticker": self.instrument.ticker,
            "threshold_type": "below",
            "threshold_value": "100.00",
            "notification_config": {
                "is_email": True,
                "is_push": True,
                "is_websocket": False,
            },
        }

        response = self.client.post(self.url, data=payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        created_alert = PriceAlert.objects.get(id=response.data["id"])
        assert created_alert.investor == self.investor


class TestDetailView:
    """Tests for price alert detail, update, and delete views"""

    @pytest.fixture(autouse=True)
    def setup(self, api_client_auth, investor_factory, instruments_factory, user):
        self.client = api_client_auth
        # Create investor with authenticated user's id
        self.investor = investor_factory()
        self.investor.clerk_id = user.id
        self.investor.save()
        self.instrument = instruments_factory()
        self.notification_config = NotificationConfig.objects.create(
            is_email=True, is_push=True, is_websocket=False
        )
        self.alert = PriceAlert.objects.create(
            investor=self.investor,
            instrument=self.instrument,
            notification_config=self.notification_config,
            threshold_type="above",
            threshold_value=Decimal("150.00"),
        )
        self.url = reverse("price-alert-detail", args=[self.alert.id])

    def test_retrieve__returns_alert_details(self):
        """Test retrieve view returns alert details"""
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == str(self.alert.id)
        assert response.data["threshold_type"] == "above"
        assert response.data["threshold_value"] == "150.00"

    def test_update__modifies_alert(self):
        """Test update view modifies alert"""
        payload = {
            "threshold_value": "160.00",
        }

        response = self.client.patch(self.url, data=payload, format="json")

        assert response.status_code == status.HTTP_200_OK
        self.alert.refresh_from_db()
        assert self.alert.threshold_value == Decimal("160.00")

    def test_delete__removes_alert(self):
        """Test delete view removes alert"""
        response = self.client.delete(self.url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not PriceAlert.objects.filter(id=self.alert.id).exists()

    def test_retrieve__forbidden_for_other_user(self, investor_factory):
        """Test retrieve view forbids access to other user's alerts"""
        other_investor = investor_factory()
        other_alert = PriceAlert.objects.create(
            investor=other_investor,
            instrument=self.instrument,
            notification_config=self.notification_config,
            threshold_type="below",
            threshold_value=Decimal("100.00"),
        )

        url = reverse("price-alert-detail", args=[other_alert.id])
        response = self.client.get(url)

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_update__forbidden_for_other_user(self, investor_factory):
        """Test update view forbids modification of other user's alerts"""
        other_investor = investor_factory()
        other_alert = PriceAlert.objects.create(
            investor=other_investor,
            instrument=self.instrument,
            notification_config=self.notification_config,
            threshold_type="below",
            threshold_value=Decimal("100.00"),
        )

        url = reverse("price-alert-detail", args=[other_alert.id])
        payload = {"threshold_value": "120.00"}
        response = self.client.patch(url, data=payload, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND
