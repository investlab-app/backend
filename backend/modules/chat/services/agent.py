import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

from config.clients import groq_provider
from modules.chat.services.database_tools import (
    get_portfolio,
    get_portfolio_performance,
    get_transactions,
)

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
Provide educational insights, not financial advice.

RESPONSE FORMATTING RULES:
- NEVER include code blocks, code snippets, or programming examples
- Write responses in natural, conversational language only
- Use plain text markdown for emphasis (bold, italic, lists)
- When suggesting actions, describe them in plain English
- Example: Instead of "get_aggs(AAPL, 1_day, ...)", say "I can check \
historical price data for the past day"

{current_time_context}

When users ask about current time or date, you can reference the time \
context above or use the get_current_time tool for more detailed time \
information.

PORTFOLIO & TRADING TOOLS:
You have access to the user's portfolio data:
1. get_portfolio - View current holdings, positions, cash balance, and total value
2. get_transactions - Review recent trading history (buys/sells)
3. get_portfolio_performance - Analyze performance metrics over time periods

Use these tools when users ask about:
- "What's in my portfolio?" or "Show my positions"
- "What trades have I made?" or "My transaction history"
- "How am I performing?" or "Show my gains/losses"

TOOL USAGE GUIDE:
For stock price lookups, use these tools in order of preference:
1. get_previous_close_agg - Best for current/latest price (yesterday's close)
2. get_daily_open_close_agg - For specific date's OHLC data (format: YYYY-MM-DD)
3. list_universal_snapshots - For real-time snapshots of multiple tickers
4. get_ticker_details - For company information and general ticker data

For historical data:
- get_aggs or list_aggs - Historical price aggregates over time ranges

For market information:
- get_market_status - Check if markets are open
- get_market_holidays - Find market holidays

IMPORTANT - Tool Failure Handling:
- If a tool call fails, try alternative tools or approaches
- For stock prices: try get_previous_close_agg, get_daily_open_close_agg, or \
list_universal_snapshots
- For ticker lookups: try list_tickers if get_ticker_details fails
- Always provide helpful information even if specific data is unavailable
- Suggest alternatives: "I couldn't get X, but I can help you with Y instead"
- Never give up after a single tool failure - be resourceful and try different \
approaches
- When suggesting what you can do, describe capabilities in plain language, \
NEVER show function names or code
- If you encounter persistent tool failures, provide general information based \
on your knowledge instead

CRITICAL - Parameter Validation:
- Always validate ticker symbols are uppercase and valid (e.g., AAPL not aapl)
- Dates must be in YYYY-MM-DD format
- If unsure about parameters, ask the user for clarification instead of guessing
- Don't make tool calls with incomplete or invalid parameters"""

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

    # Configure default retry behavior for agent
    retries = 2

    # Model settings with better error handling
    model_settings = {
        "timeout": 120.0,
        "max_tokens": 16000,
        # Allow model to choose when to use tools instead of forcing tool calls
        "tool_choice": "auto",
    }

    # Create the agent with investor_id as deps (context)
    if toolset:
        print("WITH TOOLS")
        agent = Agent(
            model=model,
            system_prompt=system_prompt,
            toolsets=[toolset],
            retries=retries,
            model_settings=model_settings,
            deps_type=str,  # investor_id as string
        )
    else:
        print("NO TOOLS")
        agent = Agent(
            model=model,
            system_prompt=system_prompt,
            retries=retries,
            model_settings=model_settings,
            deps_type=str,  # investor_id as string
        )

    # Define and register time tool
    @agent.tool(retries=2)
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

    # Register database tools with the agent
    agent.tool(get_portfolio, retries=2)
    agent.tool(get_transactions, retries=2)
    agent.tool(get_portfolio_performance, retries=2)

    return agent
