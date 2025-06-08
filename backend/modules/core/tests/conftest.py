import pytest

from modules.users.tests.conftest import user


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


@pytest.fixture
def websocket_communicator():
    from channels.testing import WebsocketCommunicator

    from config.asgi import application

    async def _create_communicator(path="/ws/test/"):
        communicator = WebsocketCommunicator(application, path)
        return communicator

    yield _create_communicator


@pytest.fixture
def websocket_communicator_auth(user):
    from channels.testing import WebsocketCommunicator

    from config.asgi import application

    async def _create_communicator(path="/ws/test/"):
        communicator = WebsocketCommunicator(application, path)
        communicator.scope["user"] = user
        return communicator

    yield _create_communicator
