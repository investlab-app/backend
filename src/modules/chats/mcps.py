from pydantic_ai.toolsets.fastmcp import FastMCPToolset
from pydantic_ai.toolsets.filtered import FilteredToolset

from config.settings import MCP_MASSIVE_URL


class MassiveMCP:
    base_toolset = FastMCPToolset(MCP_MASSIVE_URL)

    def get_toolset(self) -> FilteredToolset[None]:
        # Our subscriptions only allow a subset of tools
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

        return self.base_toolset.filtered(
            lambda ctx, tool_def: tool_def.name in allowed_tools
        )
