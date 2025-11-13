from decimal import Decimal

import pytest
from django.urls import reverse

from modules.authentication.tests.conftest import ClerkUser, user
from modules.core.tests.conftest import api_client  # noqa: F401
from modules.instruments.tests.conftest import instruments_factory
from modules.investors.tests.conftest import create_fake_investor
from modules.orders.models import Order
from modules.orders.tests.conftest import fake_limit_order

pytestmark = pytest.mark.django_db


class TestCreateLimitOrderView:
    @pytest.fixture(autouse=True)
    def setup(self, instruments_factory, user):
        self.instrument = instruments_factory()
        # give investor enough balance by default so limit orders can be created
        self.investor = create_fake_investor(
            clerk_id=user.id, balance=Decimal("100.00"), save=True
        )
        self.user = user
        self.url = reverse("limit-order")

    def test_happy(self, api_client):
        data = {
            "ticker": self.instrument.ticker,
            "volume": "10.00",
            "is_buy": True,
            "limit_price": "1.00",
        }
        api_client.force_authenticate(user=self.user)
        response = api_client.post(self.url, data, content_type="application/json")
        assert response.status_code == 201
        assert Order.objects.filter(investor=self.investor).count() == 1
        api_client.logout()

    def test_not_enough_funds(self, api_client):
        # simulate investor with low balance by updating existing investor
        self.investor.balance = Decimal("0.00")
        self.investor.save()
        data = {
            "ticker": self.instrument.ticker,
            "volume": "10.00",
            "is_buy": True,
            "limit_price": "1.00",
        }
        api_client.force_authenticate(user=self.user)
        response = api_client.post(self.url, data, content_type="application/json")
        # either 400 or 201 depending on blocked funds logic;
        # expect 400 when insufficient
        assert response.status_code == 400
        api_client.logout()


class TestDestroyLimitOrderView:
    @pytest.fixture(autouse=True)
    def setup(self, user):
        self.investor = create_fake_investor(clerk_id=user.id, save=True)
        self.user = user
        self.order = fake_limit_order(
            investor=self.investor,
            save=True,
            volume=Decimal(5),
            limit_price=Decimal("1.00"),
        )
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
        other_order = fake_limit_order(investor=other_investor, save=True)
        url = reverse("destroy-order", kwargs={"id": other_order.id})

        api_client.force_authenticate(user=self.user)
        response = api_client.delete(url)
        assert response.status_code == 404
        assert Order.objects.filter(id=other_order.id).exists()
        api_client.logout()
