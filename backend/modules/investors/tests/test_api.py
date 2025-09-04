import pytest
from django.urls import reverse

from modules.authentication.tests.conftest import user  # noqa: F401
from modules.core.tests.conftest import api_client, api_client_auth  # noqa: F401
from modules.investors.models import Investor
from modules.investors.services import InvestorsService

pytestmark = pytest.mark.django_db


class TestInvestorExpView:
    endpoint = "investors:investor-exp"

    def test_happy(self, api_client_auth, user):
        investor = Investor.objects.create(clerk_id=user.id, exp=1000)
        expected_level = str(
            InvestorsService.get_level_from_exp(investor.exp)  # ty: ignore
        )

        url = reverse(self.endpoint)
        response = api_client_auth.get(url)

        assert response.status_code == 200
        assert response.data["exp"] == 1000
        assert response.data["level"] == expected_level

    def test_auto_create_if_missing(self, api_client_auth, user):
        assert not Investor.objects.filter(clerk_id=user.id).exists()

        url = reverse(self.endpoint)
        response = api_client_auth.get(url)

        assert response.status_code == 200
        assert response.data["exp"] == 0
        assert response.data["level"] == str(InvestorsService.get_level_from_exp(0))

        assert Investor.objects.filter(clerk_id=user.id).exists()

    def test_no_auth(self, api_client):
        url = reverse(self.endpoint)
        response = api_client.get(url)
        assert response.status_code == 403
