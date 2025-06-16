from unittest.mock import MagicMock, patch

import pytest
from clerk_backend_api import SDKError
from rest_framework.test import APIRequestFactory

from modules.users.models import User


@pytest.fixture
def mock_clerk_login_serializer():
    with patch(
        "modules.authentication.views.ClerkLoginSerializer",
    ) as mock_serializer_class:
        mock_instance = MagicMock()
        mock_instance.is_valid.return_value = True
        mock_instance.validated_data = {
            "email": "test@example.com",
            "password": "correct-password",
        }
        mock_serializer_class.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def valid_payload():
    return {
        "sub": "user_123",
        "email": "test@example.com",
        "first_name": "Test",
        "last_name": "User",
        "img_url": "http://image.com/avatar.png",
        "has_img": True,
        "meta": {"role": "admin"},
    }


@pytest.fixture
def user_from_payload(valid_payload):
    return User(
        id=valid_payload["sub"],
        email=valid_payload["email"],
        first_name=valid_payload["first_name"],
        last_name=valid_payload["last_name"],
        image_url=valid_payload["img_url"],
        has_image=valid_payload["has_img"],
        clerk_role=valid_payload["meta"]["role"],
    )


@pytest.fixture
def mock_clerk(valid_payload):
    with (
        patch("modules.authentication.views.Clerk") as mock_clerk_views,
        patch("modules.authentication.clerk_auth.Clerk") as mock_clerk_auth,
    ):
        mock_clerk_instance = MagicMock()

        mock_user = MagicMock()
        mock_user.id = valid_payload["sub"]
        mock_user.email_addresses[0].email_address.return_value = valid_payload["email"]
        mock_user.first_name = valid_payload["first_name"]
        mock_user.last_name = valid_payload["last_name"]
        mock_user.image_url = valid_payload["img_url"]
        mock_user.has_image = valid_payload["has_img"]
        mock_user.public_metadata = valid_payload["meta"]
        mock_clerk_instance.users.list.return_value = [mock_user]
        mock_clerk_instance.users.get.return_value = mock_user

        mock_clerk_instance.users.verify_password.return_value = None

        mock_session = MagicMock()
        mock_session.id = "sess_456"
        mock_clerk_instance.sessions.create.return_value = mock_session

        mock_access_token = MagicMock()
        mock_access_token.jwt = "mocked-access-token"
        mock_clerk_instance.sessions.create_token.return_value = mock_access_token

        mock_clerk_views.return_value = mock_clerk_instance
        mock_clerk_auth.return_value = mock_clerk_instance
        yield mock_clerk_instance


@pytest.fixture
def mock_clerk_invalid_password():
    with patch("modules.authentication.views.Clerk") as mock_clerk_class:
        mock_clerk_instance = MagicMock()

        mock_user = MagicMock()
        mock_user.id = "user_123"
        mock_clerk_instance.users.list.return_value = [mock_user]

        mock_clerk_instance.users.verify_password.side_effect = SDKError(
            message="API error occurred",
            status_code=422,
            body='{"errors":[{"message":"incorrect password"}]}',
        )

        mock_clerk_class.return_value = mock_clerk_instance
        yield mock_clerk_instance


@pytest.fixture
def factory():
    return APIRequestFactory()


@pytest.fixture
def mock_django_cache():
    with patch("modules.authentication.clerk_auth.cache") as mock_cache:
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None
        yield mock_cache


@pytest.fixture
def mock_decode_token(mocker, valid_payload):
    return mocker.patch(
        "modules.authentication.clerk_auth.decode_token",
        return_value=valid_payload,
    )
