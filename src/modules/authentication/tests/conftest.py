from unittest.mock import MagicMock, patch

import pytest
from clerk_backend_api import SDKError
from httpx import Response
from rest_framework.test import APIRequestFactory

from modules.authentication.clerk_auth import ClerkUser


@pytest.fixture()
def user():
    return ClerkUser(
        clerk_id="id",
        role="admin",
    )


@pytest.fixture()
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


@pytest.fixture()
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


@pytest.fixture()
def user_from_payload(valid_payload):
    return ClerkUser(
        clerk_id=valid_payload["sub"],
        role=valid_payload["meta"]["role"],
    )


@pytest.fixture()
def mock_clerk(valid_payload):
    with (
        patch("modules.authentication.views.clerk_sdk") as mock_clerk_views,
        patch("modules.authentication.clerk_auth.clerk_sdk") as mock_clerk_auth,
    ):
        mock_request_state = MagicMock(
            is_signed_in=True,
            payload=valid_payload,
            token="fake-token",
        )
        mock_clerk_auth.authenticate_request.return_value = mock_request_state
        mock_clerk_views.authenticate_request.return_value = mock_request_state

        mock_user = MagicMock(
            clerk_id=valid_payload["sub"],
            public_metadata=valid_payload["meta"],
        )

        mock_clerk_auth.users.get.return_value = mock_user
        mock_clerk_views.users.get.return_value = mock_user

        mock_clerk_auth.users.list.return_value = [mock_user]
        mock_clerk_views.users.list.return_value = [mock_user]

        mock_session = MagicMock(id="sess_456")
        mock_clerk_auth.sessions.create.return_value = mock_session
        mock_clerk_views.sessions.create.return_value = mock_session

        mock_access_token = MagicMock(jwt="mocked-access-token")
        mock_clerk_auth.sessions.create_token.return_value = mock_access_token
        mock_clerk_views.sessions.create_token.return_value = mock_access_token

        yield mock_clerk_views


@pytest.fixture()
def mock_clerk_invalid_password():
    with patch("modules.authentication.views.clerk_sdk") as mock_clerk_class:
        mock_user = MagicMock()
        mock_user.clerk_id = "user_123"
        mock_clerk_class.users.list.return_value = [mock_user]

        mock_clerk_class.users.verify_password.side_effect = SDKError(
            message="API error occurred",
            raw_response=Response(
                status_code=422,
                content='{"errors":[{"message":"incorrect password"}]}',
            ),
        )

        yield mock_clerk_class


@pytest.fixture()
def factory():
    return APIRequestFactory()


@pytest.fixture()
def mock_django_cache():
    with patch("modules.authentication.clerk_auth.cache") as mock_cache:
        mock_cache.get.return_value = None
        mock_cache.set.return_value = None
        yield mock_cache
