import uuid
from unittest.mock import Mock

import pytest

from modules.sse import SSERequestParams
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
def consumer():
    return SSEConsumerImpl()


@pytest.fixture
def mock_prices():
    return {"AAPL": 150.25, "GOOGL": 2800.50, "MSFT": 300.75, "TSLA": 250.00}
