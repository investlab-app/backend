import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic_ai import Agent, RunContext
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
    # Get current time for context
    now_utc = datetime.now(ZoneInfo("UTC"))
    current_time_context = f"""
Current Date/Time Context:
- UTC: {now_utc.strftime("%Y-%m-%d %H:%M:%S %Z")}
- Date: {now_utc.strftime("%Y-%m-%d")}
- Day: {now_utc.strftime("%A")}
"""

    system_prompt = f"""You are a financial assistant for InvestLab, \
a paper trading simulator.

Help users analyze stocks and trading performance. Be concise and use \
available tools for real data.
Provide educational insights, not financial advice. Format responses in \
markdown with code examples when relevant.

{current_time_context}

When users ask about current time or date, you can reference the time \
context above or use the get_current_time tool for more detailed time \
information."""

    # Define allowed tools from Polygon API
    allowed_tools = {
        "get_aggs",
        "list_aggs",
        "get_grouped_daily_aggs",
        "get_daily_open_close_agg",
        "get_previous_close_agg",
        "list_trades",
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

    # Define and register time tool
    @agent.tool
    async def get_current_time(ctx: RunContext[None]) -> dict:
        """
        Get the current date and time information.

        Returns:
            Dictionary with current datetime in various formats and timezones.
        """
        now_utc = datetime.now(ZoneInfo("UTC"))
        now_local = datetime.now()

        return {
            "utc_iso": now_utc.isoformat(),
            "utc_readable": now_utc.strftime("%Y-%m-%d %H:%M:%S %Z"),
            "local_iso": now_local.isoformat(),
            "local_readable": now_local.strftime("%Y-%m-%d %H:%M:%S"),
            "unix_timestamp": int(now_utc.timestamp()),
            "date": now_utc.strftime("%Y-%m-%d"),
            "time": now_utc.strftime("%H:%M:%S"),
            "day_of_week": now_utc.strftime("%A"),
            "timezone": str(now_utc.tzinfo),
        }

    return agent
