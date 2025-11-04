import json
import logging
from collections.abc import AsyncGenerator, AsyncIterable

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from groq import APIError as GroqAPIError
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
)
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
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

    async def _load_message_history(self) -> list[ModelMessage]:
        """Load chat history from database and convert to agent message format."""
        messages = await sync_to_async(list)(
            ChatMessage.objects.filter(investor=self.investor)
            .order_by("created_at")
            .values("role", "content")
        )

        history = []
        for msg in messages:
            if msg["role"] == ChatMessage.ROLE_USER:
                history.append(
                    ModelRequest(parts=[UserPromptPart(content=msg["content"])])
                )
            elif msg["role"] == ChatMessage.ROLE_ASSISTANT:
                history.append(ModelResponse(parts=[TextPart(content=msg["content"])]))

        return history

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

        # Load conversation history from database
        print("LOADING HISTORY")
        message_history = await self._load_message_history()

        # Stream agent response
        print("STREAMING RESPONSE")
        await self.send_json({"type": "start", "message": "Processing your query..."})

        print("STARTING STREAM")
        try:
            full_response = ""
            chunk_count = 0
            async for chunk in self._stream_response(message, message_history):
                print(f"RECEIVED CHUNK #{chunk_count}: {repr(chunk)}")
                await self.send_json({"type": "chunk", "content": chunk})
                full_response += chunk
                chunk_count += 1

            print(
                f"STREAM COMPLETED: Total chunks = {chunk_count}, "
                f"Total length = {len(full_response)}"
            )
            logger.info(
                "Stream completed with %d chunks, total %d chars",
                chunk_count,
                len(full_response),
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

    def _handle_part_delta_event(self, event: PartDeltaEvent):
        """Handle part delta events."""
        if isinstance(event.delta, TextPartDelta):
            print(
                f"[Event] Part {event.index} text delta: {event.delta.content_delta!r}"
            )
        elif isinstance(event.delta, ThinkingPartDelta):
            print(
                f"[Event] Part {event.index} thinking delta: "
                f"{event.delta.content_delta!r}"
            )
        elif isinstance(event.delta, ToolCallPartDelta):
            print(
                f"[Event] Part {event.index} tool args delta: {event.delta.args_delta}"
            )

    async def _event_stream_handler(
        self, ctx: RunContext, event_stream: AsyncIterable[AgentStreamEvent]
    ):
        """Handle and log agent stream events with error handling."""
        try:
            async for event in event_stream:
                if isinstance(event, PartStartEvent):
                    print(f"[Event] Starting part {event.index}: {event.part!r}")
                elif isinstance(event, PartDeltaEvent):
                    self._handle_part_delta_event(event)
                elif isinstance(event, FunctionToolCallEvent):
                    print(
                        f"[Event] LLM calls tool={event.part.tool_name!r} "
                        f"with args={event.part.args} "
                        f"(tool_call_id={event.part.tool_call_id!r})"
                    )
                    logger.info(
                        "Tool call: %s with args: %s",
                        event.part.tool_name,
                        event.part.args,
                    )
                elif isinstance(event, FunctionToolResultEvent):
                    print(
                        f"[Event] Tool call {event.tool_call_id!r} returned => "
                        f"{event.result.content}"
                    )
                    result_preview = str(event.result.content)[:200]
                    logger.info(
                        "Tool result for %s: %s",
                        event.tool_call_id,
                        result_preview,
                    )
                elif isinstance(event, FinalResultEvent):
                    print(
                        f"[Event] Model producing final result "
                        f"(tool_name={event.tool_name})"
                    )
        except Exception as e:
            logger.exception("Error in event stream handler: %s", e)
            # Don't re-raise - let the main stream continue

    async def _stream_response(
        self, user_message: str, message_history: list[ModelMessage] = None
    ) -> AsyncGenerator[str]:
        """Stream response chunks from the agent."""
        if not self.agent:
            raise RuntimeError("Agent not initialized")

        print(f"RUNNING AGENT with message: {user_message}")
        print(f"HISTORY LENGTH: {len(message_history) if message_history else 0}")
        try:
            # Use run_stream to get real-time streaming responses with event handler
            # Add usage limits to prevent infinite loops
            async with self.agent.run_stream(
                user_message,
                message_history=message_history,
                event_stream_handler=self._event_stream_handler,
            ) as response:
                print("STREAMING TEXT FROM AGENT (delta mode)")
                async for text_delta in response.stream_text(delta=True):
                    delta_preview = (
                        text_delta[:50] if len(text_delta) > 50 else text_delta
                    )
                    print(f"YIELDING DELTA: {repr(delta_preview)}")
                    yield text_delta

            print("STREAM COMPLETE")

        except GroqAPIError as e:
            print(f"GROQ API ERROR: {e}")
            error_msg = str(e)

            # Try to extract more details from the error
            error_details = {
                "error_message": error_msg,
                "user_message": user_message,
                "history_length": len(message_history) if message_history else 0,
            }

            # Log detailed error information
            logger.error(
                "Groq API function call failed: %s. Details: %s",
                error_msg,
                error_details,
            )

            # Check if it's a function call error
            if "Failed to call a function" in error_msg:
                yield (
                    "I'm having trouble using the tools to fetch that "
                    "information right now. "
                    "This could be due to:\n"
                    "- Temporary API limitations\n"
                    "- Invalid parameters for the data request\n"
                    "- Market data service being unavailable\n\n"
                    "You can try:\n"
                    "- Asking a more general question\n"
                    "- Requesting different information\n"
                    "- Trying again in a moment\n"
                )
            else:
                yield (
                    "I encountered a technical issue while processing your request. "
                    "Please try rephrasing your question or ask about something else."
                )

        except UnexpectedModelBehavior as e:
            print(f"MODEL BEHAVIOR ERROR: {e}")
            logger.warning("Agent encountered unexpected behavior: %s", e)
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
