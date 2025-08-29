from typing import Any

from clerk_backend_api import AuthenticateRequestOptions
from django.conf import settings
from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from config.clerk import client as clerk_sdk
from modules.investors.models import Investor
from modules.users.models import User


def parse_user_from_payload(payload: dict[str, Any]) -> User:
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

    metadata = clerk_user.public_metadata
    email = clerk_user.email_addresses[0].email_address
    role = metadata.get("role", "investor")
    user, _ = User.objects.update_or_create(
        email=email,  # Deletion not handled; reusing email breaks uniqueness.
        defaults={
            "clerk_id": clerk_user_id,
            "first_name": clerk_user.first_name,
            "last_name": clerk_user.last_name,
            "image_url": clerk_user.image_url,
            "has_image": clerk_user.has_image,
            "clerk_role": role,
        },
    )

    Investor.objects.update_or_create(user=user)

    return user


class ClerkAuthentication(BaseAuthentication):
    """
    Custom authentication class that verifies Clerk JWTs.
    Sets `request.user` to a custom User model retrieved from database
    Sets `request.token to the retrived token`
    """

    def authenticate(self, request: Request) -> tuple[User, str | None]:
        request_state = clerk_sdk.authenticate_request(
            request,
            AuthenticateRequestOptions(
                jwt_key=settings.CLERK_JWT_KEY,
            ),
        )

        if not request_state.is_signed_in:
            raise AuthenticationFailed("User is not authenticated")

        payload = request_state.payload

        if not payload:
            raise AuthenticationFailed("User payload not found")

        user = parse_user_from_payload(payload)
        token = request_state.token

        return user, token
