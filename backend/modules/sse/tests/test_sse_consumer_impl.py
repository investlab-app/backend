import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from modules.sse import clients, live_prices
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
            "modules.sse.sse_consumer_impl.clerk_auth.validate_token"
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
        consumer._send_event = AsyncMock()

        # Setup clients dictionary with subscribed symbols
        clients[mock_connection_id] = mock_symbols

        try:
            await consumer.live_prices_handler(mock_prices)

            # Verify _send_event was called
            consumer._send_event.assert_called_once()
            call_args = consumer._send_event.call_args

            assert call_args[0][0] == "price_update"
            # Parse the sent data to verify filtering
            sent_data = call_args[0][1]
            assert "AAPL" in sent_data
            assert "GOOGL" in sent_data
            assert "TSLA" not in sent_data  # Should be filtered out

        finally:
            # Cleanup
            if mock_connection_id in clients:
                del clients[mock_connection_id]

    @pytest.mark.asyncio
    async def test_live_prices_handler_no_connection_id(self, consumer, mock_prices):
        """Test live prices handler when connection ID is not set"""
        consumer.connection_id = None

        with patch("logging.error") as mock_log_error:
            await consumer.live_prices_handler(mock_prices)

            mock_log_error.assert_called_once_with(
                "Connection ID is not set, cannot handle live prices."
            )

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
            patch("modules.sse.sse_consumer_impl.parse_sse_request") as mock_parse,
            patch("modules.sse.sse_consumer_impl.subscribe") as mock_subscribe,
            patch.object(consumer, "log") as mock_log,
            patch.object(live_prices, "add_handler") as mock_add_handler,
        ):

            # Setup mocks
            mock_parsed_params = Mock()
            mock_parsed_params.connection_id = mock_connection_id
            mock_parsed_params.symbols = mock_symbols
            mock_parse.return_value = mock_parsed_params

            # Setup clients dict to simulate successful subscription
            clients[mock_connection_id] = mock_symbols

            try:
                # Create a task that will set the shutdown event after a short delay
                async def trigger_shutdown():
                    await asyncio.sleep(0.1)
                    consumer.shutdown_event.set()

                shutdown_task = asyncio.create_task(trigger_shutdown())

                # Run the handle method
                await consumer.handle(mock_request_data)

                # Wait for shutdown task to complete
                await shutdown_task

                # Verify all expected calls were made
                mock_parse.assert_called_once_with(mock_request_data)
                mock_subscribe.assert_called_once_with(mock_connection_id, mock_symbols)
                mock_add_handler.assert_called_once_with(consumer.live_prices_handler)

                # Verify connection_id was set
                assert consumer.connection_id == mock_connection_id

                # Verify logging calls
                assert mock_log.call_count >= 2  # Start and finish logs

            finally:
                # Cleanup
                if mock_connection_id in clients:
                    del clients[mock_connection_id]

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
            patch("modules.sse.sse_consumer_impl.parse_sse_request") as mock_parse,
            patch("logging.debug") as mock_log_debug,
        ):

            # Setup mocks
            mock_parsed_params = Mock()
            mock_parsed_params.connection_id = mock_connection_id
            mock_parsed_params.symbols = mock_symbols
            mock_parse.return_value = mock_parsed_params

            # Setup clients dict
            clients[mock_connection_id] = mock_symbols

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

                # Verify the cancellation was logged
                mock_log_debug.assert_any_call(
                    f"{mock_connection_id}: Disconnected from SSE stream."
                )

            finally:
                # Cleanup
                if mock_connection_id in clients:
                    del clients[mock_connection_id]

    @pytest.mark.asyncio
    async def test_disconnect_method_success(
        self, consumer, mock_connection_id, mock_symbols
    ):
        """Test successful disconnect method execution"""
        consumer.connection_id = mock_connection_id
        consumer.shutdown_event = asyncio.Event()

        # Setup clients dict
        clients[mock_connection_id] = mock_symbols

        with (
            patch("modules.sse.sse_consumer_impl.unsubscribe") as mock_unsubscribe,
            patch("logging.debug") as mock_log_debug,
            patch.object(
                consumer.__class__.__bases__[0], "disconnect", new_callable=AsyncMock
            ) as mock_super_disconnect,
        ):

            await consumer.disconnect()

            # Verify shutdown event was set
            assert consumer.shutdown_event.is_set()

            # Verify unsubscribe was called with correct parameters
            mock_unsubscribe.assert_called_once_with(mock_connection_id, mock_symbols)

            # Verify logging
            mock_log_debug.assert_any_call(
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
            patch("modules.sse.sse_consumer_impl.unsubscribe") as mock_unsubscribe,
            patch("logging.debug") as mock_log_debug,
            patch.object(
                consumer.__class__.__bases__[0], "disconnect", new_callable=AsyncMock
            ) as mock_super_disconnect,
        ):

            await consumer.disconnect()

            # Verify unsubscribe was called with empty set
            mock_unsubscribe.assert_called_once_with(mock_connection_id, set())

            # Verify other behaviors still work
            assert consumer.shutdown_event.is_set()
            mock_log_debug.assert_called()
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
            patch("modules.sse.sse_consumer_impl.parse_sse_request") as mock_parse,
            patch("modules.sse.sse_consumer_impl.subscribe") as mock_subscribe,
            patch.object(live_prices, "add_handler") as mock_add_handler,
        ):

            # Setup mocks
            mock_parsed_params = Mock()
            mock_parsed_params.connection_id = mock_connection_id
            mock_parsed_params.symbols = mock_symbols
            mock_parse.return_value = mock_parsed_params

            # Setup empty clients dict (no active subscriptions)
            clients[mock_connection_id] = set()

            try:
                # Create a task that will set the shutdown event after a short delay
                async def trigger_shutdown():
                    await asyncio.sleep(0.1)
                    consumer.shutdown_event.set()

                shutdown_task = asyncio.create_task(trigger_shutdown())

                # Run the handle method
                await consumer.handle(mock_request_data)

                # Wait for shutdown task to complete
                await shutdown_task

                # Verify subscribe was called but add_handler was not
                mock_subscribe.assert_called_once_with(mock_connection_id, mock_symbols)
                mock_add_handler.assert_not_called()  # Should not be called for empty subscription

            finally:
                # Cleanup
                if mock_connection_id in clients:
                    del clients[mock_connection_id]

    @pytest.mark.asyncio
    async def test_live_prices_handler_filters_prices_correctly(
        self, consumer, mock_connection_id
    ):
        """Test that live prices handler correctly filters prices based on client subscriptions"""
        consumer.connection_id = mock_connection_id
        consumer._send_event = AsyncMock()

        # Setup client with specific subscriptions
        subscribed_symbols = {"AAPL", "GOOGL"}
        clients[mock_connection_id] = subscribed_symbols

        # Provide prices for both subscribed and unsubscribed symbols
        all_prices = {
            "AAPL": 150.25,
            "GOOGL": 2800.50,
            "TSLA": 250.00,  # Not subscribed
        }

        try:
            await consumer.live_prices_handler(all_prices)

            # Verify _send_event was called
            consumer._send_event.assert_called_once()

            # Extract the sent data
            call_args = consumer._send_event.call_args
            sent_data_str = call_args[0][1]

            # Verify only subscribed symbols are included
            assert "AAPL" in sent_data_str
            assert "GOOGL" in sent_data_str
            assert "TSLA" not in sent_data_str

        finally:
            # Cleanup
            if mock_connection_id in clients:
                del clients[mock_connection_id]
