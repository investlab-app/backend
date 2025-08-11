from modules.authentication.clerk_auth import verify_token
from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed
from urllib.parse import parse_qs

class JWTAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, *args, **kwargs):
        qs = parse_qs(scope['query_string'].decode())
        token = qs.get('token', [None])[0]
        try:
            scope['user'] = await sync_to_async(verify_token)(token)
        except AuthenticationFailed:
            scope['user'] = AnonymousUser()
        return await self.app(scope, *args, **kwargs)