from unittest.mock import Mock

import pytest

from modules.sse import clients


@pytest.fixture(autouse=True)
def cleanup_clients():
    """Clean up the clients dictionary after each test to avoid test pollution"""
    yield
    clients.clear()


@pytest.fixture
def mock_clerk_auth():
    """Mock the clerk_auth module for authentication tests"""
    mock_auth = Mock()
    mock_auth.validate_token.return_value = True
    mock_auth.AuthenticationFailed = Exception
    return mock_auth
