from typing import Any

from django.conf import settings
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel

from config.clients import groq_provider
from modules.chat.services.database_tools import (
    create_performance_tool,
    create_portfolio_tool,
    create_transactions_tool,
)


def create_financial_agent(investor_id: str) -> Agent:
    """
    Create a Pydantic-AI agent for financial assistance.

    The agent has access to:
    - Real-time stock data via MCP (Polygon/Massive API)
    - User portfolio and position data
    - Transaction history
    - Performance metrics

    Args:
        investor_id: The investor's UUID as string

    Returns:
        Configured Agent instance
    """

    model = OpenAIChatModel(
        "llama-3.1-8b-instant",
        provider=groq_provider,
    )

    # Create agent with system prompt
    system_prompt = """You are a helpful financial assistant for InvestLab, a paper trading application.

You have access to tools that provide:
- Real-time and historical stock market data (prices, aggregates, market status)
- User portfolio positions and holdings
- Trading history and transactions
- Performance metrics and analytics

Your responsibilities:
1. Answer questions about stocks, market data, and trading
2. Provide portfolio insights and analysis
3. Help users understand their trading performance
4. Use available tools to fetch current data for accurate responses
5. Format responses with clear markdown formatting
6. Provide financial context and educational information (NOT financial advice)

Guidelines:
- Always use real data from available tools when applicable
- Reference the user's specific portfolio when relevant
- Include appropriate disclaimers that this is paper trading simulation
- Be conversational but professional
- When uncertain about data, acknowledge the limitation
- Suggest checking market hours for real-time pricing accuracy"""

    # Create the agent
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=[
            create_portfolio_tool(),
            create_transactions_tool(),
            create_performance_tool(),
        ],
    )

    return agent


async def stream_agent_response(
    agent: Agent,
    investor_id: str,
    user_message: str,
) -> Any:
    """
    Stream a response from the financial agent.

    Args:
        agent: The configured Agent instance
        investor_id: The investor's UUID as string
        user_message: The user's message/query

    Yields:
        Response chunks from the agent
    """
    # Prepare context with investor ID for tools
    context = {
        "investor_id": investor_id,
    }

    # Stream the response
    async with agent.run_stream(
        user_message,
    ) as result:
        async for chunk in result:
            yield chunk
