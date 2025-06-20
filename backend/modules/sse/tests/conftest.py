import uuid
from unittest.mock import Mock

import pytest
from dependency_injector import containers, providers

from modules.prices.services import LivePricesService
from modules.sse.schemas import SSERequestParams
from modules.sse.sse_consumer_impl import SSEConsumerImpl


@pytest.fixture
def mock_connection_id():
    return uuid.uuid4()


@pytest.fixture
def mock_symbols():
    return {"AAPL", "GOOGL"}


@pytest.fixture
def valid_request_data(mock_connection_id, mock_symbols):
    return {
        "connectionId": str(mock_connection_id),
        "symbols": list(mock_symbols),
    }


@pytest.fixture
def mock_parsed_params(mock_connection_id, mock_symbols):
    params = Mock(spec=SSERequestParams)
    params.connection_id = mock_connection_id
    params.symbols = mock_symbols
    return params


@pytest.fixture
def mock_prices():
    return {"AAPL": 150.25, "GOOGL": 2800.50, "MSFT": 300.75, "TSLA": 250.00}


@pytest.fixture(autouse=True, scope="session")
def cleanup_test_environment():
    """Cleanup test environment after all tests."""


@pytest.fixture
def live_prices():
    return LivePricesService()


@pytest.fixture
def consumer(live_prices):
    return SSEConsumerImpl(live_prices=live_prices)
