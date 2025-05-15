import pytest
from modules.users.tests.conftest import user  # noqa: F401


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient

    yield APIClient()


@pytest.fixture
def api_client_auth(user):
    from rest_framework.test import APIClient

    client = APIClient()
    client.force_authenticate(user=user)
    yield client
    client.logout()
