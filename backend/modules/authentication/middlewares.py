from collections.abc import Mapping

from asgiref.sync import sync_to_async
from clerk_backend_api import AuthenticateRequestOptions, Requestish
from django.contrib.auth.models import AnonymousUser

from config.clerk import client as clerk_sdk
from modules.authentication.clerk_auth import parse_clerk_user_from_payload


class ClerkRequestAdapter(Requestish):
    def __init__(self, headers: Mapping[str, str]):
        self._headers = headers

    @property
    def headers(self) -> Mapping[str, str]:
        return self._headers


class CookieWebsocketAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        headers = {k.decode(): v.decode() for k, v in scope["headers"]}
        request = ClerkRequestAdapter(headers)
        request_state = clerk_sdk.authenticate_request(
            request, AuthenticateRequestOptions()
        )

        if request_state.is_signed_in:
            payload = request_state.payload
            scope["user"] = await sync_to_async(parse_clerk_user_from_payload)(payload)
        else:
            scope["user"] = AnonymousUser()

        return await self.app(scope, receive, send)
