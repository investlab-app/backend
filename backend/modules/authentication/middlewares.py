from asgiref.sync import sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.exceptions import AuthenticationFailed

from modules.authentication.clerk_auth import verify_token


class CookieWebsocketAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        headers = dict(scope["headers"])
        cookies = {}
        if b"cookie" in headers:
            cookie_header = headers[b"cookie"].decode()
            for kv in cookie_header.split(";"):
                k, v = kv.strip().split("=", 1)
                cookies[k] = v

        token = cookies.get("auth_token")
        try:
            scope["user"] = await sync_to_async(verify_token)(token)
        except AuthenticationFailed:
            scope["user"] = AnonymousUser()
        return await self.app(scope, receive, send)
