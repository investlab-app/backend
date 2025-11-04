import json
import logging
from collections.abc import AsyncGenerator

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from modules.chat.models import ChatMessage
from modules.chat.services.agent import create_financial_agent
from modules.investors.models import Investor

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time financial chat with streaming responses."""

    async def connect(self):
        """Handle WebSocket connection."""
        print("CONNECTING")
        if not self.scope["user"].is_authenticated:
            await self.accept()
            await self.close()
            return

        # Get investor instance
        print("FETCHING INVESTOR")
        self.investor = await sync_to_async(
            Investor.objects.filter(clerk_id=self.scope["user"].id).first
        )()

        print("HANDLING INVESTOR")
        if not self.investor:
            await self.accept()
            await self.send_json(
                {"type": "error", "message": "Investor profile not found"}
            )
            await self.close()
            return

        # Initialize the financial agent
        print("INITIALIZING AGENT")
        try:
            self.agent = await create_financial_agent(str(self.investor.id))
        except Exception as e:
            logger.warning("Failed to initialize chat agent: %s", e)
            self.agent = None

        print("ACCEPTING CONNECTION")
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages."""
        print("RECEIVING MESSAGE")
        if not text_data:
            return

        print("PARSING MESSAGE")
        if isinstance(text_data, (bytes, bytearray)):
            text_data = text_data.decode("utf-8")

        print("LOADING JSON")
        try:
            data = json.loads(text_data)
            message = data.get("message", "").strip()
        except (json.JSONDecodeError, AttributeError):
            await self.send_json({"type": "error", "message": "Invalid JSON format"})
            return

        print("CHECKING MESSAGE")
        if not message:
            await self.send_json(
                {"type": "error", "message": "Message cannot be empty"}
            )
            return

        # Save user message
        print("SAVING USER MESSAGE")
        await sync_to_async(ChatMessage.objects.create)(
            investor=self.investor,
            role=ChatMessage.ROLE_USER,
            content=message,
        )

        # Stream agent response
        print("STREAMING RESPONSE")
        await self.send_json({"type": "start", "message": "Processing your query..."})

        print("STARTING STREAM")
        try:
            full_response = ""
            async for chunk in self._stream_response(message):
                await self.send_json({"type": "chunk", "content": chunk})
                full_response += chunk

            # Save assistant response
            await sync_to_async(ChatMessage.objects.create)(
                investor=self.investor,
                role=ChatMessage.ROLE_ASSISTANT,
                content=full_response,
            )

            await self.send_json({"type": "end"})

        except Exception as e:
            logger.exception("Error streaming response: %s", e)
            await self.send_json({"type": "error", "message": f"Error: {str(e)}"})

    async def _stream_response(self, user_message: str) -> AsyncGenerator[str, None]:
        """Stream response chunks from the agent."""
        if not self.agent:
            raise RuntimeError("Agent not initialized")

        print("RUNNING AGENT STREAM")
        async with self.agent.run_stream(user_message) as result:
            async for text_delta in result.stream_text(delta=True):
                if text_delta:
                    yield text_delta

    async def disconnect(self, code):
        """Handle WebSocket disconnection."""
        pass
