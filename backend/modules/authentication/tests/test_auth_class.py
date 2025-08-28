import pytest
from rest_framework.exceptions import AuthenticationFailed

from modules.authentication.clerk_auth import ClerkAuthentication


@pytest.mark.django_db
def test_auth_with_valid_authorization_header(
    factory,
    user_from_payload,
    mock_clerk,
    mock_django_cache,
):
    request = factory.get("/test", HTTP_AUTHORIZATION="Bearer mock.token")
    auth = ClerkAuthentication()
    user, _ = auth.authenticate(request)

    assert user
    assert user == user_from_payload


def test_authenticate_no_bearer_no_cookie_raises_exception(factory):
    request = factory.get("/some-url/")
    auth = ClerkAuthentication()
    with pytest.raises(AuthenticationFailed):
        auth.authenticate(request)
