from pydantic_ai.toolsets.fastmcp import FastMCPToolset
from pydantic_ai.toolsets.filtered import FilteredToolset

from config.settings import MCP_ECHARTS_URL, MCP_MASSIVE_URL


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


class EChartsMCP:
    toolset = FastMCPToolset(MCP_ECHARTS_URL)

    # Some tools cause errors
    allowed_tools = [
        "generate_echarts",
        "generate_line_chart",
        "generate_bar_chart",
        "generate_pie_chart",
        "generate_radar_chart",
        "generate_scatter_chart",
        "generate_sankey_chart",
        "generate_funnel_chart",
        "generate_gauge_chart",
        # "generate_treemap_chart",
        # "generate_sunburst_chart",
        # "generate_heatmap_chart",
        "generate_candlestick_chart",
        "generate_boxplot_chart",
        "generate_parallel_chart",
        # "generate_tree_chart",
    ]

    def get_toolset(self) -> FilteredToolset[None]:
        return self.toolset.filtered(
            lambda ctx, tool_def: tool_def.name in self.allowed_tools
        )
