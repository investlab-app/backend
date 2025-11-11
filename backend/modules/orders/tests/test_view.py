from decimal import Decimal
from unittest.mock import patch

import pytest
from django.urls import reverse

from modules.authentication.tests.conftest import ClerkUser, user
from modules.core.tests.conftest import api_client, api_client_auth  # noqa: F401
from modules.instruments.tests.conftest import instruments_factory
from modules.investors.tests.conftest import create_fake_investor
from modules.orders.models import Order
from modules.orders.tests.conftest import fake_market_order

pytestmark = pytest.mark.django_db


class TestCreateMarketOrderView:
    @pytest.fixture(autouse=True)
    def setup(self, instruments_factory, user):
        self.instrument = instruments_factory()
        self.investor = create_fake_investor(clerk_id=user.id, save=True)
        self.user = user
        self.url = reverse("create-market-order")

    @patch("modules.orders.services.order_services.OrderService._get_current_price")
    def test_happy(self, _get_current_price, api_client):
        data = {
            "ticker": self.instrument.ticker,
            "volume": "10.00",
            "is_buy": True,
        }
        _get_current_price.return_value = Decimal(0)
        api_client.force_authenticate(user=self.user)
        response = api_client.post(self.url, data, content_type="application/json")
        assert response.status_code == 201
        assert Order.objects.filter(investor=self.investor).count() == 1
        api_client.logout()


class TestListOrderView:
    @pytest.fixture(autouse=True)
    def setup(self, user):
        self.investor = create_fake_investor(clerk_id=user.id, save=True)
        self.user = user
        self.orders = [
            fake_market_order(investor=self.investor, save=True) for _ in range(5)
        ]
        self.url = reverse("list-orders")

    def test_happy(self, api_client):
        api_client.force_authenticate(user=self.user)
        response = api_client.get(self.url)
        assert response.status_code == 200
        assert len(response.data["results"]) == 5
        api_client.logout()

    def test_other_user_orders_not_listed(self, api_client):
        other_user = ClerkUser(clerk_id="hehexd", role="Any")
        other_investor = create_fake_investor(clerk_id=other_user.id, save=True)
        self.orders = [fake_market_order(investor=other_investor) for _ in range(3)]

        api_client.force_authenticate(user=self.user)
        response = api_client.get(self.url)
        assert response.status_code == 200
        assert len(response.data["results"]) == 5
        api_client.logout()


class TestDestroyOrderView:
    @pytest.fixture(autouse=True)
    def setup(self, user):
        self.investor = create_fake_investor(clerk_id=user.id, save=True)
        self.user = user
        self.order = fake_market_order(investor=self.investor, save=True)
        self.url = reverse("destroy-order", kwargs={"id": self.order.id})

    def test_happy(self, api_client):
        api_client.force_authenticate(user=self.user)
        response = api_client.delete(self.url)
        assert response.status_code == 204
        assert not Order.objects.filter(id=self.order.id).exists()
        api_client.logout()

    def test_cannot_delete_other_user_order(self, api_client):
        other_user = ClerkUser(clerk_id="hehexd", role="Any")
        other_investor = create_fake_investor(clerk_id=other_user.id, save=True)
        other_order = fake_market_order(investor=other_investor, save=True)
        url = reverse("destroy-order", kwargs={"id": other_order.id})

        api_client.force_authenticate(user=self.user)
        response = api_client.delete(url)
        assert response.status_code == 404
        assert Order.objects.filter(id=other_order.id).exists()
        api_client.logout()
