from config.celery import async_task
from modules.chats.agent import AgentDeps, agent
from modules.chats.services import LLMStreamingService


@async_task()
async def respond_to_chat_message(
    investor_id: str,
    chat_id: str,
    user_message: str,
):
    deps = AgentDeps(investor_id=investor_id)
    service = LLMStreamingService(agent, investor_id=investor_id, chat_id=chat_id)
    await service.respond(
        user_message=user_message,
        deps=deps,
    )
