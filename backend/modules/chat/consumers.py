import asyncio
import json
import logging
from collections.abc import AsyncGenerator, AsyncIterable

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from pydantic_ai import (
    Agent,
    AgentStreamEvent,
    FinalResultEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    PartDeltaEvent,
    PartStartEvent,
    RunContext,
    TextPartDelta,
    ThinkingPartDelta,
    ToolCallPartDelta,
    UnexpectedModelBehavior,
    UsageLimits,
)

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

    async def _event_stream_handler(
        self, ctx: RunContext, event_stream: AsyncIterable[AgentStreamEvent]
    ):
        """Handle and log agent stream events."""
        async for event in event_stream:
            if isinstance(event, PartStartEvent):
                print(f"[Event] Starting part {event.index}: {event.part!r}")
            elif isinstance(event, PartDeltaEvent):
                if isinstance(event.delta, TextPartDelta):
                    print(
                        f"[Event] Part {event.index} text delta: {event.delta.content_delta!r}"
                    )
                elif isinstance(event.delta, ThinkingPartDelta):
                    print(
                        f"[Event] Part {event.index} thinking delta: {event.delta.content_delta!r}"
                    )
                elif isinstance(event.delta, ToolCallPartDelta):
                    print(
                        f"[Event] Part {event.index} tool args delta: {event.delta.args_delta}"
                    )
            elif isinstance(event, FunctionToolCallEvent):
                print(
                    f"[Event] LLM calls tool={event.part.tool_name!r} with args={event.part.args} (tool_call_id={event.part.tool_call_id!r})"
                )
            elif isinstance(event, FunctionToolResultEvent):
                print(
                    f"[Event] Tool call {event.tool_call_id!r} returned => {event.result.content}"
                )
            elif isinstance(event, FinalResultEvent):
                print(
                    f"[Event] Model producing final result (tool_name={event.tool_name})"
                )

    async def _stream_response(self, user_message: str) -> AsyncGenerator[str, None]:
        """Stream response chunks from the agent."""
        if not self.agent:
            raise RuntimeError("Agent not initialized")

        print(f"RUNNING AGENT with message: {user_message}")
        try:
            # Use run_stream to get real-time streaming responses with event handler
            # Add usage limits to prevent infinite loops
            async with self.agent.run_stream(
                user_message,
                event_stream_handler=self._event_stream_handler,
                usage_limits=UsageLimits(
                    request_limit=10,  # Max 10 requests to prevent infinite loops
                    total_tokens_limit=12000,  # Reasonable token limit
                ),
            ) as response:
                print("STREAMING TEXT FROM AGENT (delta mode)")
                async for text_delta in response.stream_text(delta=True):
                    print(
                        f"YIELDING DELTA: {repr(text_delta[:50] if len(text_delta) > 50 else text_delta)}"
                    )
                    yield text_delta

            print("STREAM COMPLETE")

        except UnexpectedModelBehavior as e:
            print(f"MODEL BEHAVIOR ERROR: {e}")
            logger.warning(f"Agent encountered unexpected behavior: {e}")
            # Provide a helpful fallback message
            yield (
                "I encountered an issue while processing your request. "
                "This might be due to:\n"
                "- The requested tool or data is temporarily unavailable\n"
                "- The query requires information I don't have access to\n\n"
                "Please try:\n"
                "- Rephrasing your question\n"
                "- Asking about a different topic\n"
                "- Being more specific about what you need\n"
            )
        except Exception as e:
            print(f"ERROR IN _stream_response: {type(e).__name__}: {e}")
            logger.exception("Error in _stream_response")
            raise

    async def disconnect(self, code):
        """Handle WebSocket disconnection."""
        pass
