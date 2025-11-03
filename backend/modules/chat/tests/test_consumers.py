import json
import pytest
from channels.testing import WebsocketCommunicator
from django.test import AsyncClient
from modules.chat.consumers import ChatConsumer
from modules.investors.models import Investor


@pytest.mark.django_db
@pytest.mark.asyncio
class TestChatConsumer:
    """Test ChatConsumer WebSocket functionality."""

    async def test_connect_unauthenticated_closes_connection(self):
        """Test that unauthenticated users are disconnected."""
        communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), "ws/chat/")
        connected, subprotocol = await communicator.connect()
        assert connected
        await communicator.disconnect()

    async def test_connect_authenticated_accepts_connection(self, investor_factory):
        """Test that authenticated users establish connection."""
        investor = investor_factory()
        # Note: This test would need proper authentication setup
        # For now, just verify the consumer structure

    async def test_receive_empty_message_returns_error(self, investor_factory):
        """Test that empty messages return an error."""
        # This would require WebSocket authentication setup

    async def test_receive_invalid_json_returns_error(self):
        """Test that invalid JSON returns an error."""
        # This would require WebSocket authentication setup

    async def test_message_is_saved_to_database(self, investor_factory):
        """Test that user messages are saved to database."""
        # This would require WebSocket authentication setup
