from unittest.mock import MagicMock

import pytest

from modules.authentication.tests.conftest import user  # noqa: F401
from modules.investors.tests.conftest import create_fake_investor


@pytest.fixture
def investor_factory():
    def create_investor(**kwargs):
        return create_fake_investor(**kwargs, save=True)

    return create_investor


@pytest.fixture
def mock_clerk_user_service():
    mock = MagicMock()
    mock.get_user_email_addresses.return_value = ["test@example.com"]
    return mock


@pytest.fixture
def mock_email_service():
    mock = MagicMock()
    mock.send_email = MagicMock(return_value=True)
    return mock


@pytest.fixture
def mock_push_service():
    mock = MagicMock()
    mock.send_push = MagicMock(return_value=True)
    return mock


@pytest.fixture
def mock_websocket_service():
    mock = MagicMock()
    mock.send_websocket_notification = MagicMock(return_value=True)
    return mock
