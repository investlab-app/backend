# backend/authentication/clerk_auth.py
import modules.authentication.extensions
import os
import requests
import jwt
from jwt.exceptions import PyJWTError
from jwcrypto import jwk

from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from clerk_backend_api import Clerk

from modules.users.models import User
from django.core.cache import cache


def get_jwks():
    """Fetch JWKS (JSON Web Key Set) from Clerk's endpoint"""
    try:
        response = requests.get(os.environ["CLERK_JWKS_URL"], timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise AuthenticationFailed(f"Failed to fetch JWKS: {str(e)}")


def get_public_key(kid):
    """Find the correct public key from Clerk JWKS"""
    jwks = get_jwks()
    for key in jwks['keys']:
        if key['kid'] == kid:
            return jwk.JWK(**key)
    raise AuthenticationFailed("Public key not found for given 'kid'")


def decode_token(token):
    try:
        headers = jwt.get_unverified_header(token)
        kid = headers['kid']
        public_key = get_public_key(kid)

        payload = jwt.decode(
            token,
            public_key.export_to_pem().decode('utf-8'),
            algorithms=["RS256"],
            issuer=os.environ["CLERK_ISSUER"],
        )
        return payload
    except PyJWTError as e:
        raise AuthenticationFailed(f"Token verification failed: {str(e)}")
    except Exception as e:
        raise AuthenticationFailed(f"Unexpected token error: {str(e)}")


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
        payload = decode_token(token)
        print(payload)
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationFailed("User ID (sub) not found in token")
        
        cache_key = f"clerk_user_{user_id}"
        clerk_user = cache.get(cache_key)

        if not clerk_user:
            clerk_sdk = Clerk(bearer_auth=os.environ["CLERK_SECRET_KEY"])
            clerk_user = clerk_sdk.users.get(user_id=user_id)
            cache.set(cache_key, clerk_user, timeout=300) 
        
        if not clerk_user:
            raise AuthenticationFailed("Could not retrieve clerk user")
        if not clerk_user.email_addresses or len(clerk_user.email_addresses) == 0:
            raise AuthenticationFailed("Could user does not have an email address")
            
        email = clerk_user.email_addresses[0].email_address
        role = clerk_user.public_metadata.get("role")
        user, _ = User.objects.get_or_create(email=email)
        if role not in ["admin", "investor"]:
            role = "investor"
            user.clerk_role = role
            user.save()

        return user, None
