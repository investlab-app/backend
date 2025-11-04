import asyncio
import json
import logging
from collections.abc import AsyncGenerator

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from pydantic_ai import Agent

from modules.chat.models import ChatMessage
from modules.chat.services.agent import create_financial_agent
from modules.investors.models import Investor

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncJsonWebsocketConsumer):
    """WebSocket consumer for real-time financial chat with streaming responses."""

    agent: Agent

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
            raise RuntimeError("Failed to initialize chat agent") from e

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

        if text_data == "ping":
            await self.send(text_data="pong")
            return

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
            chunk_count = 0
            async for chunk in self._stream_response(message):
                print(f"RECEIVED CHUNK #{chunk_count}: {repr(chunk)}")
                await self.send_json({"type": "chunk", "content": chunk})
                full_response += chunk
                chunk_count += 1

            print(
                f"STREAM COMPLETED: Total chunks = {chunk_count}, Total length = {len(full_response)}"
            )
            logger.info(
                f"Stream completed with {chunk_count} chunks, total {len(full_response)} chars"
            )

            # Save assistant response
            await sync_to_async(ChatMessage.objects.create)(
                investor=self.investor,
                role=ChatMessage.ROLE_ASSISTANT,
                content=full_response,
            )

            print("SENDING END MESSAGE")
            await self.send_json({"type": "end"})

        except Exception as e:
            logger.exception("Error streaming response: %s", e)
            print(f"EXCEPTION IN STREAM: {e}")
            await self.send_json({"type": "error", "message": f"Error: {str(e)}"})

    async def _stream_response(self, user_message: str) -> AsyncGenerator[str, None]:
        """Stream response chunks from the agent."""
        if not self.agent:
            raise RuntimeError("Agent not initialized")

        print("RUNNING AGENT - Getting full response first")
        try:
            # Get the complete response first to avoid truncation issues with run_stream()
            out = []
            async with self.agent.iter("get_aggs AAPL") as agent_run:
                async for node in agent_run:
                    print(f"AGG NODE: {node}")
                    out.append(str(node))

            result = "".join(out)

            full_text = result

            print(f"GOT FULL RESPONSE: {len(full_text)} characters")
            print(f"Response preview: {repr(full_text[:100])}")

            # Now stream it in chunks to the frontend
            chunk_size = 50  # Stream in 50-character chunks
            chunk_count = 0

            for i in range(0, len(full_text), chunk_size):
                chunk = full_text[i : i + chunk_size]
                print(f"YIELDING CHUNK #{chunk_count}: {repr(chunk[:50])}")
                yield chunk
                chunk_count += 1

            print(
                f"STREAM COMPLETE - Yielded {chunk_count} chunks, total {len(full_text)} chars"
            )

        except Exception as e:
            print(f"ERROR IN _stream_response: {type(e).__name__}: {e}")
            logger.exception("Error in _stream_response")
            raise

    async def disconnect(self, code):
        """Handle WebSocket disconnection."""
        pass
