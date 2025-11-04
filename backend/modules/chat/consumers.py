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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.investor = None
        self.agent = None
        self.investor_id = None

    async def connect(self):
        """Handle WebSocket connection."""
        if not self.scope["user"].is_authenticated:
            await self.accept()
            await self.close()
            return

        clerk_id = self.scope["user"].id

        # Get investor instance
        self.investor = await sync_to_async(
            Investor.objects.filter(clerk_id=clerk_id).first
        )()

        if not self.investor:
            await self.accept()
            await self.send_json(
                {
                    "type": "error",
                    "message": "Investor profile not found",
                }
            )
            await self.close()
            return

        self.investor_id = str(self.investor.id)

        # Initialize the financial agent
        try:
            self.agent = await create_financial_agent(self.investor_id)
        except Exception as e:
            await self.accept()
            logger.warning("Failed to initialize chat agent: %s", e)
            await self.send_json(
                {
                    "type": "warning",
                    "message": (
                        "Chat initialized with limited features. "
                        "Some tools may not be available."
                    ),
                }
            )

        await self.accept()
        logger.info("Chat connection established for investor %s", self.investor_id)

    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming WebSocket messages."""
        if text_data is None:
            return

        if isinstance(text_data, (bytes, bytearray)):
            text_data = text_data.decode("utf-8")

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_json(
                {
                    "type": "error",
                    "message": "Invalid JSON format",
                }
            )
            return

        message = data.get("message", "").strip()

        if not message:
            await self.send_json(
                {
                    "type": "error",
                    "message": "Message cannot be empty",
                }
            )
            return

        # Save user message to database
        await sync_to_async(ChatMessage.objects.create)(
            investor=self.investor,
            role=ChatMessage.ROLE_USER,
            content=message,
        )

        # Send start signal
        await self.send_json(
            {
                "type": "start",
                "message": "Processing your query...",
            }
        )

        # Stream agent response
        try:
            full_response = ""
            chunk_count = 0
            async for chunk in self._stream_response(message):
                chunk_count += 1
                logger.debug(
                    "Streaming chunk #%s: %s, length=%s, accumulated_length=%s",
                    chunk_count,
                    repr(chunk[:100]),
                    len(chunk),
                    len(full_response) + len(chunk),
                )
                await self.send_json(
                    {
                        "type": "chunk",
                        "content": chunk,
                    }
                )
                full_response += chunk

            logger.debug(
                "Streaming complete. Total chunks: %s, Final response length: %s",
                chunk_count,
                len(full_response),
            )

            # Save assistant response to database
            await sync_to_async(ChatMessage.objects.create)(
                investor=self.investor,
                role=ChatMessage.ROLE_ASSISTANT,
                content=full_response,
            )

            # Send completion signal
            await self.send_json(
                {
                    "type": "end",
                }
            )

        except Exception as e:
            logger.exception("Error streaming response: %s", e)
            await self.send_json(
                {
                    "type": "error",
                    "message": f"Error processing your query: {str(e)}",
                }
            )

    async def _stream_response(self, user_message: str) -> AsyncGenerator[str]:
        """Stream response chunks from the agent."""
        try:
            chunk_count = 0
            async with self.agent.run_stream(user_message) as result:
                async for text_delta in result.stream_text(delta=True):
                    if text_delta:
                        chunk_count += 1
                        logger.debug(
                            "_stream_response yielding delta chunk #%s: %s, length=%s",
                            chunk_count,
                            repr(text_delta[:100]),
                            len(text_delta),
                        )
                        yield text_delta
        except Exception as e:
            logger.exception("Error in agent stream: %s", e)
            raise

    async def disconnect(self, code):
        """Handle WebSocket disconnection."""
        logger.info(
            "Chat connection closed for investor %s with code %s",
            self.investor_id,
            code,
        )
