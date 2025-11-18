import logging
from dataclasses import dataclass

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

from config.settings import GEMINI_API_KEY
from modules.chats.models import Chat, ChatMessage

logger = logging.getLogger(__name__)


@dataclass
class ChatMessageDTO:
    id: str
    role: str
    timestamp: str
    content: str


class ChatMessagesService:
    async def get_messages(self, chat_id: str) -> list[ModelMessage]:
        chat = await Chat.objects.aget(id=chat_id)
        messages: list[ModelMessage] = []

        async for msg in ChatMessage.objects.filter(
            chat=chat, message_list__isnull=False
        ).order_by("created_at"):
            model_messages = ModelMessagesTypeAdapter.validate_json(msg.message_list)
            messages.extend(model_messages)

        return messages

    def sync_get_messages(self, chat_id: str) -> list[ModelMessage]:
        return async_to_sync(self.get_messages)(chat_id)

    def to_chat_message(self, m: ModelMessage) -> ChatMessageDTO | None:
        for first_part in m.parts:
            if isinstance(m, ModelRequest) and isinstance(first_part, UserPromptPart):
                assert isinstance(first_part.content, str)
                return ChatMessageDTO(
                    id=m.timestamp.isoformat(),
                    role="user",
                    timestamp=m.timestamp.isoformat(),
                    content=first_part.content,
                )
            elif isinstance(m, ModelResponse) and isinstance(first_part, TextPart):
                return ChatMessageDTO(
                    id=m.timestamp.isoformat(),
                    role="assistant",
                    timestamp=m.timestamp.isoformat(),
                    content=first_part.content,
                )

        return None


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
                async for text in response.stream_text(delta=True):
                    yield text

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
