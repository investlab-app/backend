import logging
from typing import Any

from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel

from config.clients import groq_provider
from modules.chat.services.database_tools import (
    create_performance_tool,
    create_portfolio_tool,
    create_transactions_tool,
)
from modules.chat.services.mcp_massive_client import MCPMassiveClient

logger = logging.getLogger(__name__)

# Global MCP client instance
_mcp_client: MCPMassiveClient | None = None


async def get_mcp_client() -> MCPMassiveClient:
    """Get or initialize the global MCP client."""
    global _mcp_client

    if _mcp_client is None:
        _mcp_client = MCPMassiveClient()
        await _mcp_client.initialize()

    return _mcp_client


async def create_financial_agent(investor_id: str) -> Agent:
    """
    Create a Pydantic-AI agent for financial assistance with MCP integration.

    The agent has access to:
    - Real-time stock data via Massive API (MCP)
    - User portfolio and position data
    - Transaction history
    - Performance metrics
    - Comprehensive market analysis tools

    Args:
        investor_id: The investor's UUID as string

    Returns:
        Configured Agent instance with MCP tools
    """

    model = GroqModel("llama-3.1-8b-instant", provider=groq_provider)

    # Initialize database tools
    database_tools = [
        create_portfolio_tool(),
        create_transactions_tool(),
        create_performance_tool(),
    ]

    # Initialize MCP Massive API tools
    mcp_tools = []
    try:
        mcp_client = await get_mcp_client()
        mcp_tools = mcp_client.create_tools()
        logger.info(f"Loaded {len(mcp_tools)} MCP tools from Massive API")
    except Exception as e:
        logger.warning(
            f"Failed to initialize MCP tools: {e}. Continuing with database tools only."
        )
        mcp_tools = []

    # Combine all tools
    all_tools = database_tools + mcp_tools

    # Create agent with system prompt
    system_prompt = """You are a financial assistant for InvestLab paper trading.

This application simulates stock market trading.

You have access to tools that provide:
- User portfolio positions and holdings
- Trading history and transactions
- Performance metrics and analytics
- Real-time stock quotes and market data via Massive API
- Stock search and company information
- Market indices and movers
- Sector performance analysis
- Technical analysis indicators
- News and market insights

Your responsibilities:
1. Answer questions about stocks, market data, and trading
2. Provide portfolio insights and analysis
3. Help users understand their trading performance
4. Search for stocks and provide comprehensive company information
5. Analyze market trends and identify opportunities
6. Use available tools to fetch current data for accurate responses
7. Format responses with clear markdown formatting
8. Provide financial context and educational information (NOT financial advice)

Guidelines:
- Always use real data from available tools when applicable
- Reference the user's specific portfolio when relevant
- Include appropriate disclaimers that this is paper trading simulation
- Be conversational but professional
- When uncertain about data, acknowledge the limitation
- Suggest checking market hours for real-time pricing accuracy
- Use Massive API tools for comprehensive stock research and market analysis
- Cross-reference multiple data sources for better insights
- Provide context about market conditions and trends
- When using Massive API tools, they fetch data directly from the market"""

    # Create the agent
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        tools=all_tools,
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
    # Stream the response
    async with agent.run_stream(
        user_message,
    ) as result:
        async for chunk in result:
            yield chunk
