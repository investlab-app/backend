from unittest.mock import MagicMock, patch

import pytest
from clerk_backend_api import SDKError
from jwcrypto import jwk
from rest_framework.test import APIRequestFactory

from modules.users.models import User


@pytest.fixture
def mock_clerk_login_serializer():
    with patch(
        "modules.authentication.views.ClerkLoginSerializer"
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
def mock_clerk():
    with patch("modules.authentication.views.Clerk") as mock_clerk_class:
        mock_clerk_instance = MagicMock()

        mock_user = MagicMock()
        mock_user.id = "user_123"
        mock_clerk_instance.users.list.return_value = [mock_user]

        mock_clerk_instance.users.verify_password.return_value = None

        mock_session = MagicMock()
        mock_session.id = "sess_456"
        mock_clerk_instance.sessions.create.return_value = mock_session

        mock_access_token = MagicMock()
        mock_access_token.jwt = "mocked-access-token"
        mock_clerk_instance.sessions.create_token.return_value = mock_access_token

        mock_clerk_class.return_value = mock_clerk_instance
        yield mock_clerk_instance


@pytest.fixture
def mock_clerk_invalid_password():
    with patch("modules.authentication.views.Clerk") as mock_clerk_class:
        mock_clerk_instance = MagicMock()

        # Mock user list returns one user
        mock_user = MagicMock()
        mock_user.id = "user_123"
        mock_clerk_instance.users.list.return_value = [mock_user]

        # Raise SDKError on password verification
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
def mock_decode_token(mocker, valid_payload):
    return mocker.patch(
        "modules.authentication.clerk_auth.decode_token", return_value=valid_payload
    )


@pytest.fixture
def mock_token():
    return "eyJhbGciOiJSUzI1NiIsImNhdCI6ImNsX0I3ZDRQRDExMUFBQSIsImtpZCI6Imluc18yeE1Za3o5TGp1OEgyMzZEUHl3R1g5QUhwczMiLCJ0eXAiOiJKV1QifQ.eyJlbWFpbCI6Im15QHdwLnBsIiwiZXhwIjoxNzQ4MTY3NTY5LCJmaXJzdF9uYW1lIjpudWxsLCJmdmEiOls5OTk5OSwtMV0sImhhc19pbWciOmZhbHNlLCJpYXQiOjE3NDgxNjM5NjksImlkIjoidXNlcl8yeFhSTEZ3b0pGWmNWUFFRZWxWaVdOTDJTR0MiLCJpbWdfdXJsIjoiaHR0cHM6Ly9pbWcuY2xlcmsuY29tL2V5SjBlWEJsSWpvaVpHVm1ZWFZzZENJc0ltbHBaQ0k2SW1sdWMxOHllRTFaYTNvNVRHcDFPRWd5TXpaRVVIbDNSMWc1UVVod2N6TWlMQ0p5YVdRaU9pSjFjMlZ5WHpKNFdGSk1SbmR2U2taYVkxWlFVVkZsYkZacFYwNU1NbE5IUXlKOSIsImlzcyI6Imh0dHBzOi8vY2hhcm1lZC1mbGVhLTc1LmNsZXJrLmFjY291bnRzLmRldiIsImp0aSI6ImY4ZDEyOGNjOTM1ZDI2MTVmOTY0IiwibGFzdF9uYW1lIjpudWxsLCJtZXRhIjp7InJvbGUiOiJhZG1pbiJ9LCJuYmYiOjE3NDgxNjM5NTksInNpZCI6InNlc3NfMnhhNmo2TjdjMTlpeG9XRUN6MVVnOTZtR2RPIiwic3ViIjoidXNlcl8yeFhSTEZ3b0pGWmNWUFFRZWxWaVdOTDJTR0MifQ.pJrac-bSJXm8L2Y06QAB_zFD9NwCM_fs6sS06ilCaG2nkOsuSgoyCWnVvfYrPscr3bENOMHtopeXZnKwm__UOhdMyUP8NXCzbViUtteynmRDZzId1OIo3CazmVKj8UM7ZtQLQ8GuC9WOMjtNyLGQC49S5f8iW-MqacsBCrHKgLwegG_KymDtN8hrzX6bXnD7x85nb4pxm7XXDmkIraLIQp1WvYW-goih5lI3ONmcaJCB0pFDsWgy2746qB5e64N4hiW099MAoufU4LD6IfMY7YyX7n2lX5EgktfR3I9sgQ9afMfTgeqnSnmb8pgMsZ-5v7iLFlSS2FAB7IoIju8zgA"


@pytest.fixture
def mock_token_decoded():
    return {
        "email": "my@wp.pl",
        "exp": 1748167569,
        "first_name": None,
        "fva": [99999, -1],
        "has_img": False,
        "iat": 1748163969,
        "id": "user_2xXRLFwoJFZcVPQQelViWNL2SGC",
        "img_url": "https://img.clerk.com/eyJ0eXBlIjoiZGVmYXVsdCIsImlpZCI6Imluc18yeE1Za3o5TGp1OEgyMzZEUHl3R1g5QUhwczMiLCJyaWQiOiJ1c2VyXzJ4WFJMRndvSkZaY1ZQUVFlbFZpV05MMlNHQyJ9",
        "iss": "https://charmed-flea-75.clerk.accounts.dev",
        "jti": "f8d128cc935d2615f964",
        "last_name": None,
        "meta": {"role": "admin"},
        "nbf": 1748163959,
        "sid": "sess_2xa6j6N7c19ixoWECz1Ug96mGdO",
        "sub": "user_2xXRLFwoJFZcVPQQelViWNL2SGC",
    }


@pytest.fixture
def mock_get_public_key(mocker):
    return mocker.patch(
        "modules.authentication.clerk_auth._get_public_key",
        return_value=jwk.JWK(
            **{
                "use": "sig",
                "kty": "RSA",
                "kid": "ins_2xMYkz9Lju8H236DPywGX9AHps3",
                "alg": "RS256",
                "n": "u2ULDHyagFpFCLpkMsX1lARycMJJVbqcmcTUX3Y-QNcGxSoPV59yImVIr6pUsiUrmTpKh91GokEEtKLGDhOHXqlnvTr8XYBcVPsYAypw76-gCVLak4xr4j1foaiswuwf1BGE5aG4XSqWUo6JjOim8k2r5MMy_LLEn1ey8F38aI4RCmSOSmaFmGnuHkyMvudGiUKwUoJMpjzgc7ewNw7-m9RIcY0hkjYoI5jdOp4obAKArvPywPSHEYUOtkEnJRCBIFAAQRmOpBk3WXP-4VKBVG6HyH6I5gmsaC9mWV_tx7EpOnJX_KC6hS8TvXFo85eK3R0PuZR5Ef1gG4lrjTg2cQ",
                "e": "AQAB",
            }
        ),
    )
