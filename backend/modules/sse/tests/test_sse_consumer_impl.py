import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from modules.sse import live_prices
from modules.sse.sse_consumer_impl import SSEConsumerImpl


class TestSSEConsumerImpl:
    """Test cases for SSEConsumerImpl"""

    def test_initialization(self, consumer):
        """Test that SSEConsumerImpl initializes correctly"""
        assert consumer.shutdown_event is not None
        assert isinstance(consumer.shutdown_event, asyncio.Event)
        assert consumer.connection_id is None
        assert not consumer.shutdown_event.is_set()

    @pytest.mark.asyncio()
    async def test_validate_auth_success(self):
        """Test successful authentication validation"""
        test_token = "valid_test_token"

        with patch(
            "modules.sse.sse_consumer_impl.clerk_auth.authenticate_and_get_user"
        ) as mock_validate:
            mock_validate.return_value = True

            result = await SSEConsumerImpl._validate_auth(test_token)

            assert result is True
            mock_validate.assert_called_once_with(test_token)

    @pytest.mark.asyncio()
    async def test_disconnect_method_success(
        self, consumer, mock_connection_id, mock_symbols
    ):
        """Test successful disconnect method execution"""
        consumer.connection_id = mock_connection_id
        consumer.shutdown_event = asyncio.Event()

        # Setup clients dict with ClientInfo
        from modules.prices.schemas import ClientInfo

        live_prices.set_client(
            mock_connection_id, ClientInfo(instruments=mock_symbols, handler=None)
        )

        with patch.object(
            consumer.__class__.__bases__[0], "disconnect", new_callable=AsyncMock
        ) as mock_super_disconnect:
            await consumer.disconnect()

            # Verify shutdown event was set
            assert consumer.shutdown_event.is_set()

            # Verify parent disconnect was called
            mock_super_disconnect.assert_called_once()

    @pytest.mark.asyncio()
    async def test_live_prices_handler_filters_prices(
        self, consumer, mock_connection_id
    ):
        """
        Test that live prices handler correctly filters prices based on client
        subscriptions.
        """
        consumer.connection_id = mock_connection_id
        consumer.send_event = Mock()

        # Setup client with specific subscriptions
        subscribed_symbols = {"AAPL", "GOOGL"}

        live_prices.subscribe(mock_connection_id, subscribed_symbols)

        # Provide prices for both subscribed and unsubscribed symbols
        all_prices = {
            "AAPL": 150.25,
            "GOOGL": 2800.50,
            "TSLA": 250.00,
        }

        try:
            consumer.live_prices_handler(all_prices)

            # Verify send_event was called
            consumer.send_event.assert_called_once()

            # Extract the sent data
            call_args = consumer.send_event.call_args
            sent_data_str = call_args[0][1]

            # Verify only subscribed symbols are included
            assert "AAPL" in sent_data_str
            assert "GOOGL" in sent_data_str
            assert "TSLA" in sent_data_str

        finally:
            # Cleanup
            live_prices.unsubscribe(mock_connection_id)
            live_prices.shutdown()
