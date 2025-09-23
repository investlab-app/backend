from typing import Any

from clerk_backend_api import AuthenticateRequestOptions
from django.conf import settings
from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from config.clerk import client as clerk_sdk
from modules.investors.models import Investor


class ClerkUser:
    def __init__(self, clerk_id, role):
        self.id = clerk_id
        self.role = role
        self.is_authenticated = True


def parse_clerk_user_from_payload(payload: dict[str, Any]) -> ClerkUser:
    clerk_user_id = payload.get("sub")
    if not clerk_user_id:
        raise AuthenticationFailed("User ID (sub) not found in token")

    cache_key = f"clerk_user_{clerk_user_id}"
    clerk_user = cache.get(cache_key)

    if not clerk_user:
        clerk_user = clerk_sdk.users.get(user_id=clerk_user_id)
        cache.set(cache_key, clerk_user, timeout=300)

    if not clerk_user:
        raise AuthenticationFailed("Could not retrieve clerk user")

    role = clerk_user.public_metadata.get("role", "user")
    Investor.objects.update_or_create(clerk_id=clerk_user_id)
    return ClerkUser(clerk_user_id, role)


class ClerkAuthentication(BaseAuthentication):
    """
    Custom authentication class that verifies Clerk JWTs.
    Sets `request.user` to a custom ClerkUser class not saved in the database
    Sets `request.token to the retrieved token`
    """

    def authenticate(self, request: Request) -> tuple[ClerkUser, str | None]:
        print("Authenticating request with ClerkAuthentication")
        request_state = clerk_sdk.authenticate_request(
            request,
            AuthenticateRequestOptions(
                jwt_key=settings.CLERK_JWT_KEY,
            ),
        )

        print("Request state:", request_state)
        if not request_state.is_signed_in:
            raise AuthenticationFailed("User is not authenticated")

        payload = request_state.payload

        print("Payload:", payload)
        if not payload:
            raise AuthenticationFailed("User payload not found")

        clerk_user = parse_clerk_user_from_payload(payload)
        print("Clerk user:", clerk_user)
        token = request_state.token
        return clerk_user, token
