from modules.authentication.clerk_auth import ClerkAuthentication, decode_token


def test_auth_with_valid_authorization_header(
    factory, mock_decode_token, user_from_payload, mock_clerk, mock_django_cache
):
    request = factory.get("/test", HTTP_AUTHORIZATION="Bearer mock.token")
    auth = ClerkAuthentication()
    user, _ = auth.authenticate(request)

    assert user
    assert user == user_from_payload
    mock_decode_token.assert_called_once()


def test_authenticate_no_bearer_no_cookie_returns_none(factory):
    request = factory.get("/some-url/")
    auth = ClerkAuthentication()
    response = auth.authenticate(request)
    assert response == (None, None)
