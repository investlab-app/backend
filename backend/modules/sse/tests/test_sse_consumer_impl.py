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

    @pytest.mark.asyncio
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

    @pytest.mark.asyncio
    async def test_live_prices_handler_success(
        self, consumer, mock_connection_id, mock_symbols, mock_prices
    ):
        """Test live prices handler processes prices correctly"""
        consumer.connection_id = mock_connection_id
        consumer.send_event = AsyncMock()

        # Setup clients dictionary with subscribed symbols
        from modules.prices.schemas import ClientInfo

        live_prices.subscribe(mock_connection_id, mock_symbols)

        try:
            await consumer.live_prices_handler(mock_prices)

            # Verify send_event was called
            consumer.send_event.assert_called_once()
            call_args = consumer.send_event.call_args

            assert call_args[0][0] == "price_update"
            # Parse the sent data to verify filtering
            sent_data = call_args[0][1]
            assert "AAPL" in sent_data
            assert "GOOGL" in sent_data
            assert "TSLA" not in sent_data  # Should be filtered out

        finally:
            # Cleanup
            live_prices.unsubscribe(mock_connection_id)
            live_prices.shutdown()

    @pytest.mark.asyncio
    async def test_live_prices_handler_no_connection_id(self, consumer, mock_prices):
        """Test live prices handler when connection ID is not set"""
        consumer.connection_id = None
        consumer.send_event = AsyncMock()

        with patch("modules.sse.sse_consumer_impl.logging") as mock_logging:
            await consumer.live_prices_handler(mock_prices)

            mock_logging.error.assert_called_once_with(
                "Connection ID is not set, cannot handle live prices."
            )
            consumer.send_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_method_success(
        self, consumer, mock_connection_id, mock_symbols
    ):
        """Test successful handle method execution"""
        mock_request_data = {
            "connectionId": str(mock_connection_id),
            "symbols": list(mock_symbols),
        }

        with (
            patch("modules.sse.sse_consumer_impl.SSERequestParams.parse") as mock_parse,
            patch(
                "modules.sse.sse_consumer_impl.live_prices.subscribe"
            ) as mock_subscribe,
            patch("modules.sse.sse_consumer_impl.logging") as mock_logging,
        ):

            # Setup mocks
            mock_parsed_params = Mock()
            mock_parsed_params.connection_id = mock_connection_id
            mock_parsed_params.symbols = mock_symbols
            mock_parse.return_value = mock_parsed_params

            live_prices.subscribe(mock_connection_id, mock_symbols)

            try:
                await consumer.handle(mock_request_data)

                mock_subscribe.assert_called_once_with(mock_connection_id, mock_symbols)
                mock_logging.debug.assert_called()

            finally:
                # Cleanup
                live_prices.unsubscribe(mock_connection_id)
                live_prices.shutdown()

    @pytest.mark.asyncio
    async def test_handle_method_with_cancellation(
        self, consumer, mock_connection_id, mock_symbols
    ):
        """Test handle method handles cancellation gracefully"""
        mock_request_data = {
            "connectionId": str(mock_connection_id),
            "symbols": list(mock_symbols),
        }

        with (
            patch("modules.sse.sse_consumer_impl.SSERequestParams.parse") as mock_parse,
            patch("modules.sse.sse_consumer_impl.logging") as mock_logging,
            patch(
                "modules.sse.sse_consumer_impl.live_prices.unsubscribe"
            ) as mock_unsubscribe,
        ):

            # Setup mocks
            mock_parsed_params = Mock()
            mock_parsed_params.connection_id = mock_connection_id
            mock_parsed_params.symbols = mock_symbols
            mock_parse.return_value = mock_parsed_params

            # Setup clients dict with ClientInfo
            from modules.prices.schemas import ClientInfo

            live_prices.subscribe(mock_connection_id, mock_symbols)

            try:
                # Create a task that will cancel the handle task
                async def cancel_task():
                    await asyncio.sleep(0.1)
                    handle_task.cancel()

                handle_task = asyncio.create_task(consumer.handle(mock_request_data))
                cancel_task_ref = asyncio.create_task(cancel_task())

                # Expect CancelledError to be raised
                with pytest.raises(asyncio.CancelledError):
                    await handle_task

                await cancel_task_ref

                mock_unsubscribe.assert_called_once_with(mock_connection_id, set())

            finally:
                # Cleanup
                live_prices.unsubscribe(mock_connection_id)
                live_prices.shutdown()

    @pytest.mark.asyncio
    async def test_disconnect_method_success(
        self, consumer, mock_connection_id, mock_symbols
    ):
        """Test successful disconnect method execution"""
        consumer.connection_id = mock_connection_id
        consumer.shutdown_event = asyncio.Event()

        # Setup clients dict with ClientInfo
        from modules.prices.schemas import ClientInfo

        live_prices.clients[mock_connection_id] = ClientInfo(
            instruments=mock_symbols, handler=None
        )

        with (
            patch("modules.sse.sse_consumer_impl.logging") as mock_logging,
            patch.object(
                consumer.__class__.__bases__[0], "disconnect", new_callable=AsyncMock
            ) as mock_super_disconnect,
        ):

            await consumer.disconnect()

            # Verify shutdown event was set
            assert consumer.shutdown_event.is_set()

            # Verify logging
            mock_logging.debug.assert_any_call(
                f"{mock_connection_id}: Disconnecting SSE stream."
            )

            # Verify parent disconnect was called
            mock_super_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_method_with_no_client_symbols(
        self, consumer, mock_connection_id
    ):
        """Test disconnect method when no client symbols exist"""
        consumer.connection_id = mock_connection_id
        consumer.shutdown_event = asyncio.Event()

        # Don't add anything to clients dict

        with (
            patch("modules.sse.sse_consumer_impl.logging") as mock_logging,
            patch.object(
                consumer.__class__.__bases__[0], "disconnect", new_callable=AsyncMock
            ) as mock_super_disconnect,
        ):

            await consumer.disconnect()

            # Verify other behaviors still work
            assert consumer.shutdown_event.is_set()
            mock_logging.debug.assert_called()
            mock_super_disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_method_with_empty_client_subscription(
        self, consumer, mock_connection_id, mock_symbols
    ):
        """Test handle method when client has no active subscriptions"""
        mock_request_data = {
            "connectionId": str(mock_connection_id),
            "symbols": list(mock_symbols),
        }

        with (
            patch("modules.sse.sse_consumer_impl.SSERequestParams.parse") as mock_parse,
            patch("modules.sse.live_prices.subscribe") as mock_subscribe,
            patch(
                "modules.sse.sse_consumer_impl.live_prices.unsubscribe"
            ) as mock_unsubscribe,
        ):

            # Setup mocks
            mock_parsed_params = Mock()
            mock_parsed_params.connection_id = mock_connection_id
            mock_parsed_params.symbols = mock_symbols
            mock_parse.return_value = mock_parsed_params

            # Setup empty clients dict (no active subscriptions)
            from modules.prices.schemas import ClientInfo

            live_prices.subscribe(mock_connection_id, set())

            try:
                await consumer.handle(mock_request_data)

                mock_subscribe.assert_called_once_with(mock_connection_id, mock_symbols)
                mock_unsubscribe.assert_called_once_with(mock_connection_id, set())

            finally:
                # Cleanup
                live_prices.unsubscribe(mock_connection_id)
                live_prices.shutdown()

    @pytest.mark.asyncio
    async def test_live_prices_handler_filters_prices_correctly(
        self, consumer, mock_connection_id
    ):
        """Test that live prices handler correctly filters prices based on client subscriptions"""
        consumer.connection_id = mock_connection_id
        consumer.send_event = AsyncMock()

        # Setup client with specific subscriptions
        subscribed_symbols = {"AAPL", "GOOGL"}

        live_prices.subscribe(mock_connection_id, subscribed_symbols)

        # Provide prices for both subscribed and unsubscribed symbols
        all_prices = {
            "AAPL": 150.25,
            "GOOGL": 2800.50,
            "TSLA": 250.00,  # Not subscribed
        }

        try:
            await consumer.live_prices_handler(all_prices)

            # Verify send_event was called
            consumer.send_event.assert_called_once()

            # Extract the sent data
            call_args = consumer.send_event.call_args
            sent_data_str = call_args[0][1]

            # Verify only subscribed symbols are included
            assert "AAPL" in sent_data_str
            assert "GOOGL" in sent_data_str
            assert "TSLA" not in sent_data_str

        finally:
            # Cleanup
            live_prices.unsubscribe(mock_connection_id)
            live_prices.shutdown()
