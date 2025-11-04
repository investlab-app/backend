import logging

from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

from config.clients import groq_provider

logger = logging.getLogger(__name__)

gpt_oss = "openai/gpt-oss-20b"
llama = "llama-3.1-8b-instant"
scout = "meta-llama/llama-4-scout-17b-16e-instruct"
qwen = "qwen/qwen3-32b"

model = GroqModel(
    qwen,
    provider=groq_provider,
)


async def create_financial_agent(investor_id: str) -> Agent:
    system_prompt = """You are a financial assistant for InvestLab, a paper trading simulator.

Help users analyze stocks and trading performance. Be concise and use available tools for real data.
Provide educational insights, not financial advice. Format responses in markdown with code examples when relevant."""

    # Define allowed tools from Polygon API
    allowed_tools = {
        "get_aggs",
        "list_aggs",
        "get_grouped_daily_aggs",
        "get_daily_open_close_agg",
        "get_previous_close_agg",
        "list_trades",
        "get_last_trade",
        "list_universal_snapshots",
        "get_snapshot_all",
        "get_snapshot_direction",
        "get_market_holidays",
        "get_market_status",
        "list_tickers",
        "get_ticker_details",
        "list_ticker_news",
    }

    # Initialize the FastMCPToolset
    try:
        # Use the Docker service name instead of localhost
        base_toolset = FastMCPToolset("http://mcp-massive:8000/mcp")

        # Filter tools using Pydantic AI's .filtered() method
        toolset = base_toolset.filtered(
            lambda ctx, tool_def: tool_def.name in allowed_tools
        )

        logger.info(
            "Successfully initialized FastMCPToolset with filtered Polygon API tools"
        )
    except Exception as e:
        logger.error("Failed to initialize FastMCPToolset: %s", e)
        # Create agent without tools if MCP server is not available
        toolset = None

    # Create the agent
    if toolset:
        print("WITH TOOLS")
        # tools:
        agent = Agent(
            model=model,
            system_prompt=system_prompt,
            toolsets=[toolset],
            model_settings={"timeout": 60.0, "max_tokens": 1500},
        )
    else:
        print("NO TOOLS")
        agent = Agent(
            model=model,
            system_prompt=system_prompt,
            model_settings={"timeout": 60.0, "max_tokens": 1500},
        )

    return agent
