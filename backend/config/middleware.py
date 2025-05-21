from functools import wraps
from django.http import JsonResponse
from jwcrypto import jwk  # Requires jwcrypto package
import os
import jwt
from jwt.exceptions import PyJWTError
from clerk_backend_api import Clerk
import requests

def get_jwks():
    """Fetch JWKS (JSON Web Key Set) from Clerk's endpoint"""
    try:
        response = requests.get(os.environ["CLERK_JWKS_URL"], timeout=5)  # Added timeout
        response.raise_for_status()  # Raises HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to fetch JWKS: {str(e)}")

def get_public_key(kid):
    """Get the public key matching the given key ID (kid) from JWKS"""
    try:
        jwks = get_jwks()
        
        # Find the key with matching kid
        for key in jwks['keys']:
            if key['kid'] == kid:
                return jwk.JWK(**key)  # Construct JWK object
        
        raise ValueError(f"Key with kid {kid} not found in JWKS")
        
    except (KeyError, TypeError) as e:
        raise ValueError(f"Invalid JWKS format: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error retrieving public key: {str(e)}")

def decode_token(token):
    try:
        # Get unverified headers to extract key ID (kid)
        headers = jwt.get_unverified_header(token)
        kid = headers['kid']
        
        # Retrieve the corresponding public key
        public_key = get_public_key(kid)
        
        # Decode and verify the JWT
        payload = jwt.decode(
            token,
            public_key.export_to_pem().decode('utf-8'),
            algorithms=["RS256"],
            issuer=os.environ["CLERK_ISSUER"]
        )
        return payload
        
    except PyJWTError as e:
        raise ValueError(f"Token verification failed: {str(e)}")
    except Exception as e:
        raise ValueError(f"Unexpected error during token decoding: {str(e)}")

def clerk_authenticated(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        # Extract the Bearer token from the Authorization header
        auth_header = request.headers.get("Authorization")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse({"error": "Authentication required"}, status=401)
        
        try:
            token = auth_header.split(" ")[1]  # Get the token part after "Bearer "
            
            # Decode and verify the token
            payload = decode_token(token)
            user_id = payload.get("sub")
            
            if not user_id:
                return JsonResponse({"error": "User ID not found in token"}, status=401)

            # Retrieve user details from Clerk
            clerk_sdk = Clerk(bearer_auth=os.environ["CLERK_SECRET_KEY"])
            print("I hate myself")
            user_details = clerk_sdk.users.get(user_id=user_id)
            print(user_details)
            # Attach user details to the request for further use
            request.user_details = user_details

        except ValueError as e:
            return JsonResponse({"error": str(e)}, status=401)
        except Exception as e:  # Catch other potential errors
            return JsonResponse({"error": "Invalid token or authentication failed"}, status=401)

        return view_func(request, *args, **kwargs)

    return wrapper