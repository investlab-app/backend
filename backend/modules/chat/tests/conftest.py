import pytest
from modules.chat.models import ChatMessage
from modules.investors.models import Investor


@pytest.fixture
def chat_message_factory():
    """Factory for creating ChatMessage instances."""

    def create_message(
        investor, role=ChatMessage.ROLE_USER, content="Test message", *, save=False
    ):
        message = ChatMessage(
            investor=investor,
            role=role,
            content=content,
        )
        if save:
            message.save()
        return message

    return create_message


@pytest.fixture
def user_chat_messages(investor_factory, chat_message_factory):
    """Create a conversation thread for testing."""
    investor = investor_factory()
    messages = [
        chat_message_factory(
            investor=investor,
            role=ChatMessage.ROLE_USER,
            content="What is the current price of AAPL?",
            save=True,
        ),
        chat_message_factory(
            investor=investor,
            role=ChatMessage.ROLE_ASSISTANT,
            content="Based on current market data, AAPL is trading at $150.25.",
            save=True,
        ),
        chat_message_factory(
            investor=investor,
            role=ChatMessage.ROLE_USER,
            content="Show me my portfolio",
            save=True,
        ),
    ]
    return messages
