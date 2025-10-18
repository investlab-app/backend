import pytest
from django.urls import reverse
from rest_framework import status

from modules.core.tests.conftest import api_client_auth  # noqa: F401


@pytest.mark.django_db
class TestVapidPublicKeyView:
    """Tests for VAPID public key endpoint"""

    @pytest.fixture(autouse=True)
    def setup(self, api_client_auth):
        self.client = api_client_auth
        self.url = reverse("notifications:vapid-public-key")

    def test_retrieve__returns_public_key(self):
        """Test that endpoint returns VAPID public key"""
        response = self.client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert "public_key" in response.data

    def test_retrieve__public_key_is_string(self):
        """Test that public key is a string"""
        response = self.client.get(self.url)

        assert isinstance(response.data["public_key"], str)

    def test_retrieve__public_key_not_empty(self):
        """Test that public key is not empty"""
        response = self.client.get(self.url)

        assert response.data["public_key"]  # Non-empty string check
