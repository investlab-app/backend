import logging
from uuid import uuid4

import httpx
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from pydantic_ai import (
    Agent,
    ModelMessage,
    ModelMessagesTypeAdapter,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

from config.clients import openai_client
from config.settings import GEMINI_API_KEY, OPENAI_TITLE_MODEL
from modules.chats.models import Chat, ChatMessage
from modules.chats.schema import ChatMessageSchema

logger = logging.getLogger(__name__)


class ChatService:
    def generate_title(self, prompt: str) -> str:
        response = openai_client.chat.completions.create(
            model=OPENAI_TITLE_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": """Role: Title Generator
Output: ONLY the title text. NO quotes. Use language from user prompt.
Constraint: Max 30 characters total.

Examples:
"Explain my investment portfolio" -> Investment Portfolio Analysis
"Generate a chart for my portfolio" -> Portfolio Chart
"Cześć" -> Cześć""",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=30,
        )
        return response.choices[0].message.content.strip()


class ChatMessagesService:
    async def get_messages(self, chat_id: str) -> list[ModelMessage]:
        chat = await Chat.objects.aget(id=chat_id)
        messages: list[ModelMessage] = []

        async for msg in ChatMessage.objects.filter(
            chat=chat, message_list__isnull=False
        ).order_by("created_at"):
            message_data = msg.message_list
            model_messages = ModelMessagesTypeAdapter.validate_json(message_data)
            messages.extend(model_messages)

        return messages

    def sync_get_messages(self, chat_id: str) -> list[ModelMessage]:
        return async_to_sync(self.get_messages)(chat_id)

    def convert_messages_to_schema(
        self, messages: list[ModelMessage]
    ) -> list[ChatMessageSchema]:
        schema_messages = []
        for msg in messages:
            if isinstance(msg, ModelRequest):
                converted = self._get_user_prompt(msg)
                if converted:
                    schema_messages.append(converted)
            elif isinstance(msg, ModelResponse):
                converted = self._get_agent_response(msg)
                if converted:
                    schema_messages.append(converted)
        return schema_messages

    def _get_user_prompt(self, msg: ModelRequest) -> ChatMessageSchema | None:
        for part in msg.parts:
            if isinstance(part, UserPromptPart):
                return ChatMessageSchema(
                    id=msg.run_id or f"unknown-id-{uuid4()}",
                    role="user",
                    content=str(part.content),  # No complex input for now
                    createdAt=part.timestamp,
                )

    def _get_agent_response(self, msg: ModelResponse) -> ChatMessageSchema | None:
        for part in msg.parts:
            if isinstance(part, TextPart):
                return ChatMessageSchema(
                    id=msg.run_id or f"unknown-id-{uuid4()}",
                    role="assistant",
                    content=part.content,
                    createdAt=msg.timestamp,
                )


class LLMStreamingService[AgentDepsT, OutputDataT]:
    def __init__(
        self,
        agent: Agent[AgentDepsT, OutputDataT],
        investor_id: str,
        chat_id: str,
        chat_messages_service: ChatMessagesService | None = None,
    ):
        self.agent = agent
        self.investor_id = investor_id
        self.chat_id = chat_id
        self.chat_messages_service = chat_messages_service or ChatMessagesService()
        self.channel_layer = get_channel_layer()
        self.group_name = f"investor_{investor_id}"

    async def respond(
        self,
        user_message: str,
        deps: AgentDepsT,
    ):
        await self.send({"state": "start"})

        async for chunk in self.stream(user_message, deps):
            await self.send({"state": "streaming", "chunk": chunk})

        await self.send({"state": "end"})

    async def stream(self, user_message: str, deps: AgentDepsT):
        messages = await self.chat_messages_service.get_messages(chat_id=self.chat_id)

        # Create entirely new client per request to avoid issues with concurrency (https://github.com/pydantic/pydantic-ai/issues/748)
        async with httpx.AsyncClient() as http_client:
            provider = GoogleProvider(api_key=GEMINI_API_KEY, http_client=http_client)
            model = GoogleModel("gemini-2.5-flash", provider=provider)

            async with self.agent.run_stream(
                user_message,
                model=model,
                message_history=messages,
                deps=deps,
            ) as response:
                async for chunk in response.stream_text(delta=True):
                    yield chunk

        await ChatMessage.objects.acreate(
            chat_id=self.chat_id,
            message_list=response.new_messages_json(),
        )

    async def send(self, data: dict):
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "send.llm",
                "data": data,
            },
        )
