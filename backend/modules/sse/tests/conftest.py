import uuid
from unittest.mock import Mock

import pytest

from modules.sse import SSERequestParams
from modules.sse.sse_consumer_impl import SSEConsumerImpl


@pytest.fixture
def mock_connection_id():
    """
    Generates a unique UUID to simulate a connection identifier for testing purposes.
    
    Returns:
        A UUID object representing a mock connection ID.
    """
    return uuid.uuid4()


@pytest.fixture
def mock_symbols():
    """
    Provides a set of mock stock symbols for testing.
    
    Returns:
        A set containing example stock symbols.
    """
    return {"AAPL", "GOOGL"}


@pytest.fixture
def valid_request_data(mock_connection_id, mock_symbols):
    """
    Creates a dictionary representing a valid SSE request payload using the provided connection ID and symbols.
    
    Args:
        mock_connection_id: The unique identifier for the connection.
        mock_symbols: An iterable of stock symbols to include in the request.
    
    Returns:
        A dictionary with 'connectionId' as a string and 'symbols' as a list of symbols.
    """
    return {
        "connectionId": str(mock_connection_id),
        "symbols": list(mock_symbols),
    }


@pytest.fixture
def mock_parsed_params(mock_connection_id, mock_symbols):
    """
    Creates a mock SSERequestParams object with predefined connection ID and symbols.
    
    Returns:
        A mock object simulating SSERequestParams with connection_id and symbols attributes set.
    """
    params = Mock(spec=SSERequestParams)
    params.connection_id = mock_connection_id
    params.symbols = mock_symbols
    return params


@pytest.fixture
def consumer():
    """
    Provides an instance of the SSEConsumerImpl for use in tests.
    """
    return SSEConsumerImpl()


@pytest.fixture
def mock_prices():
    """
    Provides a dictionary of mock stock prices for use in tests.
    
    Returns:
        A dictionary mapping stock symbols to their mock price values.
    """
    return {"AAPL": 150.25, "GOOGL": 2800.50, "MSFT": 300.75, "TSLA": 250.00}
