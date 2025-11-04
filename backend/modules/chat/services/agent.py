import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.toolsets.fastmcp import FastMCPToolset

from config.clients import groq_provider

logger = logging.getLogger(__name__)

gpt_oss = "openai/gpt-oss-20b"
llama = "llama-3.1-8b-instant"
scout = "meta-llama/llama-4-scout-17b-16e-instruct"
qwen = "qwen/qwen3-32b"

model = GroqModel(
    scout,
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

IMPORTANT - Tool Failure Handling:
- If a tool call fails, try alternative tools or approaches
- For stock prices: try get_stock_price, get_daily_open_close_agg, or \
list_universal_snapshots
- For ticker lookups: try list_tickers if get_ticker_details fails
- Always provide helpful information even if specific data is unavailable
- Suggest alternatives: "I couldn't get X, but I can help you with Y instead"
- Never give up after a single tool failure - be resourceful and try different approaches
- When suggesting what you can do, describe capabilities in plain language, \
NEVER show function names or code"""

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

    # Create the agent
    if toolset:
        print("WITH TOOLS")
        agent = Agent(
            model=model,
            system_prompt=system_prompt,
            toolsets=[toolset],
            retries=retries,
            model_settings={"timeout": 60.0, "max_tokens": 1500},
        )
    else:
        print("NO TOOLS")
        agent = Agent(
            model=model,
            system_prompt=system_prompt,
            retries=retries,
            model_settings={"timeout": 60.0, "max_tokens": 1500},
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

    # Add a wrapper tool for price lookups with better error handling
    @agent.tool(retries=3)
    async def get_stock_price(ctx: RunContext[None], ticker: str) -> dict:
        """
        Get the current price and details for a stock ticker.

        Args:
            ticker: The stock ticker symbol (e.g., 'AAPL', 'GOOGL')

        Returns:
            Dictionary with price information including current price, change, volume, etc.
        """
        if not toolset:
            raise ModelRetry(
                "Price lookup service is currently unavailable. "
                "Please try again later or ask about something else."
            )

        try:
            # Use the filtered toolset to get ticker details
            # This wraps the MCP tool call with better error handling
            ticker = ticker.upper().strip()

            # Try to get snapshot first (real-time data)
            try:
                from datetime import date

                today = date.today().isoformat()

                # Get daily snapshot which includes price info
                result = await toolset.call_tool(
                    ctx, "get_daily_open_close_agg", {"ticker": ticker, "date": today}
                )

                if isinstance(result, dict) and "error" in result:
                    raise ModelRetry(
                        f"Unable to fetch price for {ticker}. "
                        f"Please verify the ticker symbol is correct. "
                        f"Common tickers include: AAPL, GOOGL, MSFT, TSLA, AMZN."
                    )

                return result

            except Exception as e:
                logger.warning(f"Failed to get snapshot for {ticker}: {e}")
                # Fallback: try to get ticker details instead
                raise ModelRetry(
                    f"Could not retrieve current price for {ticker}. "
                    f"This might be due to: market being closed, invalid ticker symbol, "
                    f"or temporary service issues. Try asking for: "
                    f"1) A different ticker symbol, "
                    f"2) Historical data instead, or "
                    f"3) General information about the company."
                )

        except ModelRetry:
            # Re-raise ModelRetry so the LLM can try again with different params
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_stock_price for {ticker}: {e}")
            raise ModelRetry(
                f"An unexpected error occurred while fetching price data. "
                f"Error details: {str(e)[:100]}. "
                f"Please try rephrasing your question or ask about a different stock."
            )

    return agent
