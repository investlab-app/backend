from dataclasses import dataclass
from datetime import date

from asgiref.sync import sync_to_async
from pydantic_ai import Agent, RunContext

from config.clients import clerk_client
from modules.chats.mcps import EChartsMCP, MassiveMCP
from modules.investors.models import Investor
from modules.investors.services import InvestorStatsService
from modules.statistics.services.transaction_stats_service import (
    TransactionStatsService,
)

echarts_mcp = EChartsMCP()
massive_mcp = MassiveMCP()


@dataclass
class AgentDeps:
    investor_id: str


agent = Agent[AgentDeps, str](
    deps_type=AgentDeps,
    system_prompt=(
        "You are a financial assistant for InvestLab, a paper trading simulator. "
        "When providing image URLs rewrite to markdown link i.e. ![Alt text](url)."
        "Please use the language of the user."
    ),
    toolsets=[
        echarts_mcp.get_toolset(),
        massive_mcp.get_toolset(),
    ],
)


@agent.system_prompt
async def add_the_users_first_name(ctx: RunContext[AgentDeps]) -> str:
    investor = await sync_to_async(Investor.objects.get)(id=ctx.deps.investor_id)
    user = await sync_to_async(clerk_client.users.get)(user_id=investor.clerk_id)
    if not user:
        return "The user's name is unknown."
    return f"The user's name is {user.first_name}."


@agent.system_prompt
def add_the_date() -> str:
    return f"The date is {date.today()}."


@agent.tool
async def get_total_value(ctx: RunContext[AgentDeps]) -> str:
    """
    Get the total value of the investor's portfolio, including cash balance and
    current value of all assets.
    """
    investor = await Investor.objects.aget(id=ctx.deps.investor_id)
    total_value = await sync_to_async(InvestorStatsService().get_total_value)(investor)
    return str(total_value)


async def get_total_assets_value(ctx: RunContext[AgentDeps]) -> str:
    """
    Get the total current market value of all assets held by the investor,
    excluding cash balance.
    """
    investor = await Investor.objects.aget(id=ctx.deps.investor_id)
    total_assets_value = await sync_to_async(
        InvestorStatsService().get_total_assets_value
    )(investor)
    return str(total_assets_value)


@agent.tool
async def get_asset_allocation(ctx: RunContext[AgentDeps]) -> str:
    """
    Get the current asset allocation of the investor's portfolio.
    Returns a list of assets with their percentage of the total portfolio,
    price per share, and total value.
    """
    investor = await Investor.objects.aget(id=ctx.deps.investor_id)
    asset_allocation = await sync_to_async(InvestorStatsService().get_asset_allocation)(
        investor
    )
    return str(asset_allocation)


@agent.tool
async def get_stats(ctx: RunContext[AgentDeps]) -> str:
    """
    Get trading statistics for the investor, including gains/losses,
    transaction counts, and volume for each ticker.
    """
    investor = await Investor.objects.aget(id=ctx.deps.investor_id)
    stats = await sync_to_async(TransactionStatsService().get_stats)(investor)
    return str(stats)
