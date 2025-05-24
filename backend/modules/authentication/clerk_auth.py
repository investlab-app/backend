import os
import requests
import jwt
from jwt.exceptions import PyJWTError

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from clerk_backend_api import Clerk

from modules.users.models import User
from django.core.cache import cache
from jwcrypto import jwk

def _get_jwks():
    try:
        response = requests.get(os.environ["CLERK_JWKS_URL"], timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise AuthenticationFailed(f"Failed to fetch JWKS: {str(e)}") from e


def _get_public_key(kid):
    jwks = _get_jwks()
    for key in jwks['keys']:
        if key['kid'] == kid:
            return jwk.JWK(**key)
    raise AuthenticationFailed("Public key not found for given 'kid'")

def _decode_token(token):
    try:
        headers = jwt.get_unverified_header(token)
        kid = headers['kid']
        public_key = _get_public_key(kid)
        payload = jwt.decode(
            token,
            public_key.export_to_pem().decode('utf-8'),
            algorithms=["RS256"],
            issuer=os.environ["CLERK_ISSUER"],
        )
        return payload
    except PyJWTError as e:
        raise AuthenticationFailed(f"Token verification failed: {str(e)}") from e
    except Exception as e:
        raise AuthenticationFailed(f"Unexpected token error: {str(e)}") from e 

def _parse_user_from_payload(payload) -> User:

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationFailed("User ID (sub) not found in token")

    email = payload.get("email")
    if not email:
        raise AuthenticationFailed("Email not found in token")

    metadata = payload.get("metadata", {})
    role = metadata.get("role", "investor")
    print("UIYSTDGFHJFDH")
    user = User(
        id=user_id,
        email=email,
        first_name=payload.get("first_name", ""),
        last_name=payload.get("last_name", ""),
        image_url=payload.get("img_url", ""),
        has_image=payload.get("has_img", False),
        clerk_role=role,
    )

    return user




class ClerkAuthentication(BaseAuthentication):
    """
    Custom authentication class that verifies Clerk JWTs.
    Sets `request.user` to a custom User model retrieved from database
    """
    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            token = request.COOKIES.get("__session")
            if not token:
                return None
        else:
            token = auth_header.split(" ")[1]
            if token == 'null':
                return None
        payload = _decode_token(token)
        user = _parse_user_from_payload(payload)
        return user, None
