import pytest
from django.urls import reverse
from rest_framework import status

from modules.core.tests.conftest import api_client
from modules.users.tests.conftest import user


def test_clerk_sign_in_success(api_client, mock_clerk, mock_clerk_login_serializer):
    url = reverse("clerk-sign-in")
    payload = {"email": "test@example.com", "password": "securepassword123"}

    response = api_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_200_OK
    assert response.data["access_token"] == "mocked-access-token"
    assert response.data["session_id"] == "sess_456"


def test_clerk_sign_in_wrong_password(
    api_client,
    mock_clerk_invalid_password,
    mock_clerk_login_serializer,
):
    url = reverse("clerk-sign-in")
    payload = {"email": "test@example.com", "password": "securepassword123"}

    response = api_client.post(url, payload, format="json")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
