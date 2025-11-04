import logging

from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio
from pydantic_ai.models.groq import GroqModel

from config.clients import groq_provider

logger = logging.getLogger(__name__)


model = GroqModel("llama-3.1-8b-instant", provider=groq_provider)


async def create_financial_agent(investor_id: str) -> Agent:
    """Create a financial agent with MCP tools for market data and portfolio analysis."""
    toolsets = []

    try:
        # Connect to MCP server using StdioTransport
        massive_mcp = MCPServerStdio(
            command="uvx",
            args=[
                "--from",
                "git+https://github.com/massive-com/mcp_massive@v0.6.0",
                "mcp_massive",
            ],
        )
        toolsets.append(massive_mcp)
        logger.info("MCP tools initialized successfully")
    except Exception as e:
        logger.warning("Failed to initialize MCP tools, continuing without them: %s", e)

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

    # Create the agent with toolsets
    agent = Agent(
        model=model,
        system_prompt=system_prompt,
        toolsets=toolsets if toolsets else None,
    )

    return agent
