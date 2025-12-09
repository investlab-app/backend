from datetime import datetime

import pytest

from modules.authentication.tests.conftest import user


@pytest.fixture(autouse=True)
def disable_throttling(settings):
    settings.REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []
    return settings


@pytest.fixture()
def api_client():
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture()
def api_client_auth(user):
    from rest_framework.test import APIClient

    client = APIClient()
    client.force_authenticate(user=user)
    yield client
    client.logout()


@pytest.fixture()
def websocket_communicator():
    from channels.testing import WebsocketCommunicator

    from config.asgi import application

    async def _create_communicator(path="/ws/test/"):
        communicator = WebsocketCommunicator(application, path)
        return communicator

    return _create_communicator


@pytest.fixture()
def websocket_communicator_auth(user):
    from channels.testing import WebsocketCommunicator

    from config.asgi import application

    async def _create_communicator(path="/ws/test/"):
        communicator = WebsocketCommunicator(application, path)
        communicator.scope["user"] = user
        return communicator

    return _create_communicator


@pytest.fixture
def year():
    def date_year(year):
        return datetime(year=year, month=1, day=1)

    return date_year
