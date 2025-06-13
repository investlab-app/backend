import jwt
import requests
from clerk_backend_api import Clerk
from django.conf import settings
from django.core.cache import cache
from jwcrypto import jwk
from jwt.exceptions import PyJWTError
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from modules.users.models import User


def _get_jwks():
    try:
        response = requests.get(settings.CLERK_JWKS_URL, timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise AuthenticationFailed(f"Failed to fetch JWKS: {e!s}") from e


def _get_public_key(kid):
    jwks = _get_jwks()
    for key in jwks["keys"]:
        if key["kid"] == kid:
            return jwk.JWK(**key)
    raise AuthenticationFailed("Public key not found for given 'kid'")


def decode_token(token):
    """Decodes and verifies a Clerk-issued JWT.

    This function extracts the `kid` (key ID) from the token header, retrieves the
    corresponding public key from Clerk's JWKS endpoint, and uses it to verify and
    decode the token. It ensures the token was signed with RS256 and issued by the
    expected Clerk issuer.

    Args:
    ----
        token (str): The JWT to decode.

    Returns:
    -------
        dict: The decoded JWT payload if the token is valid.

    Raises:
    ------
        AuthenticationFailed: If the token is invalid, expired, has incorrect
        padding, signature issues, or if the public key could not be retrieved.

    """
    try:
        headers = jwt.get_unverified_header(token)
        kid = headers["kid"]
        public_key = _get_public_key(kid)
        payload = jwt.decode(
            token,
            public_key.export_to_pem().decode("utf-8"),
            algorithms=["RS256"],
            issuer=settings.CLERK_ISSUER,
        )
        return payload
    except PyJWTError as e:
        raise AuthenticationFailed(f"Token verification failed: {e!s}") from e
    except Exception as e:
        raise AuthenticationFailed(f"Unexpected token error: {e!s}") from e


def _parse_user_from_payload(payload) -> User:
    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationFailed("User ID (sub) not found in token")

    cache_key = f"clerk_user_{user_id}"
    clerk_user = cache.get(cache_key)

    if not clerk_user:
        clerk_sdk = Clerk(bearer_auth=settings.CLERK_SECRET_KEY)
        clerk_user = clerk_sdk.users.get(user_id=user_id)
        cache.set(cache_key, clerk_user, timeout=300)

    if not clerk_user:
        raise AuthenticationFailed("Could not retrieve clerk user")

    metadata = clerk_user.public_metadata
    role = metadata.get("role", "investor")
    user = User(
        id=user_id,
        email=clerk_user.email_addresses[0].email_address,
        first_name=clerk_user.first_name,
        last_name=clerk_user.last_name,
        image_url=clerk_user.image_url,
        has_image=clerk_user.has_image,
        clerk_role=role,
    )

    return user


class ClerkAuthentication(BaseAuthentication):
    """Custom authentication class that verifies Clerk JWTs.
    Sets `request.user` to a custom User model retrieved from database
    Sets `request.token to the retrived token`
    """

    def authenticate(self, request) -> tuple[User | None, str | None]:
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            token = request.COOKIES.get("__session")
            if not token:
                return None, None
        else:
            token = auth_header.split(" ")[1]
            if token == "null":
                return None, None
        payload = decode_token(token)
        user = _parse_user_from_payload(payload)
        return user, token
