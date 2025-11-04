import logging

from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

from config.clients import groq_provider

logger = logging.getLogger(__name__)

gpt_oss = "openai/gpt-oss-20b"
llama = "llama-3.1-8b-instant"
scout = "meta-llama/llama-4-scout-17b-16e-instruct"

model = GroqModel(scout, provider=groq_provider)


async def create_financial_agent(investor_id: str) -> Agent:
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

    # Initialize the FastMCPToolset
    try:
        # Use the Docker service name instead of localhost
        toolset = FastMCPToolset("http://mcp-massive:8000/mcp")
        logger.info("Successfully initialized FastMCPToolset")
    except Exception as e:
        logger.error("Failed to initialize FastMCPToolset: %s", e)
        # Create agent without tools if MCP server is not available
        toolset = None

    # Create the agent
    if toolset:
        print("WITH TOOLS")
        agent = Agent(
            model=model,
            system_prompt=system_prompt,
            toolsets=[toolset],
        )
    else:
        print("NO TOOLS")
        agent = Agent(
            model=model,
            system_prompt=system_prompt,
        )

    return agent
