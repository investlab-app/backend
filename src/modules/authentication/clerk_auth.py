from typing import Any

from clerk_backend_api import AuthenticateRequestOptions
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from config.clients import clerk_client as clerk_sdk
from modules.investors.models import Investor


class ClerkUser:
    def __init__(self, clerk_id, role):
        self.id = clerk_id
        self.role = role
        self.is_authenticated = True

    @property
    def pk(self):
        return self.id


def parse_clerk_user_from_payload(payload: dict[str, Any]) -> ClerkUser:
    clerk_user_id = payload.get("sub")
    role = payload.get("role", "user")
    return ClerkUser(clerk_id=clerk_user_id, role=role)


class ClerkAuthentication(BaseAuthentication):
    """
    Custom authentication class that verifies Clerk JWTs.
    Sets `request.user` to a custom ClerkUser class not saved in the database
    Sets `request.token to the retrieved token`
    """

    def authenticate(self, request: Request) -> tuple[ClerkUser, str | None]:
        request_state = clerk_sdk.authenticate_request(
            request,
            AuthenticateRequestOptions(
                jwt_key=settings.CLERK_JWT_KEY,
            ),
        )

        if not request_state.is_signed_in:
            raise AuthenticationFailed("User is not signed in")

        payload = request_state.payload
        if not payload:
            raise AuthenticationFailed("Token valid but payload missing")

        clerk_user = parse_clerk_user_from_payload(payload)

        if not request.META.get("CLERK_INVESTOR_SYNCED"):
            Investor.objects.get_or_create(clerk_id=clerk_user.id)
            request.META["CLERK_INVESTOR_SYNCED"] = True

        token = request_state.token

        return clerk_user, token
