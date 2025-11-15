from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal

from asgiref.sync import sync_to_async
from pydantic_ai import Agent, RunContext

from config.clerk import client as clerk_client
from modules.chats.mcps import MassiveMCP
from modules.investors.models import Asset, Investor
from modules.prices.repositories import PolygonPricesRepository
from modules.transactions.models import Transaction

massive_mcp = MassiveMCP()


@dataclass
class AgentDeps:
    investor_id: str


agent = Agent[AgentDeps, str](
    deps_type=AgentDeps,
    system_prompt=(
        "You are a financial assistant for InvestLab, a paper trading simulator."
    ),
    toolsets=[
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


# TODO: Refactor tool functions


@agent.tool
async def get_portfolio(ctx: RunContext[AgentDeps]) -> dict:
    investor_id = ctx.deps.investor_id
    investor = await sync_to_async(Investor.objects.get)(id=investor_id)

    def get_assets():
        return list(Asset.objects.filter(investor=investor).select_related("ticker"))

    assets = await sync_to_async(get_assets)()

    if not assets:
        return {
            "status": "success",
            "balance": str(investor.balance),
            "positions": [],
            "total_value": str(investor.balance),
        }

    # Get current prices
    tickers = [a.ticker.ticker.upper() for a in assets]
    prices_repo = PolygonPricesRepository()
    prices = await sync_to_async(prices_repo.get_prices_map)(tickers)

    if prices is None:
        return {
            "status": "error",
            "message": "Failed to fetch current prices",
        }

    positions = []
    total_holdings_value = Decimal(0)

    for asset in assets:
        ticker_upper = asset.ticker.ticker.upper()
        current_price = prices[ticker_upper].current_price
        position_value = asset.volume * current_price
        total_holdings_value += position_value

        positions.append(
            {
                "ticker": asset.ticker.ticker,
                "quantity": str(asset.volume),
                "current_price": str(current_price),
                "position_value": str(position_value),
                "percentage_of_portfolio": None,  # Will calculate after
            }
        )

    total_portfolio_value = investor.balance + total_holdings_value

    # Calculate percentages
    for position in positions:
        value = Decimal(position["position_value"])
        pct = (
            (value / total_portfolio_value * 100)
            if total_portfolio_value > 0
            else Decimal(0)
        )
        position["percentage_of_portfolio"] = str(pct)

    return {
        "status": "success",
        "balance": str(investor.balance),
        "cash_percentage": str(
            (investor.balance / total_portfolio_value * 100)
            if total_portfolio_value > 0
            else Decimal(0)
        ),
        "holdings_value": str(total_holdings_value),
        "total_value": str(total_portfolio_value),
        "positions": positions,
    }


@agent.tool
async def get_transactions(ctx: RunContext[AgentDeps], limit: int = 20) -> dict:
    """
    Get recent transactions (trades) for the investor.

    Args:
        limit: Maximum number of transactions to return (default 20)

    Returns:
        Dictionary with transaction history
    """
    investor_id = ctx.deps.investor_id
    investor = await sync_to_async(Investor.objects.get)(id=investor_id)

    def get_txns():
        return list(
            Transaction.objects.filter(investor=investor)
            .select_related("ticker")
            .order_by("-timestamp")[:limit]
        )

    transaction_queryset = await sync_to_async(get_txns)()

    transaction_list = [
        {
            "id": str(t.id),
            "ticker": t.ticker.ticker,
            "type": "BUY" if t.is_buy else "SELL",
            "quantity": str(t.volume),
            "price": str(t.price),
            "total_value": str(t.volume * t.price),
            "timestamp": t.timestamp.isoformat(),
        }
        for t in transaction_queryset
    ]

    return {
        "status": "success",
        "count": len(transaction_list),
        "transactions": transaction_list,
    }


@agent.tool
async def get_portfolio_performance(
    ctx: RunContext[AgentDeps], period_days: int = 30
) -> dict:
    """
    Get portfolio performance metrics for a given period.

    Args:
        period_days: Number of days to look back (default 30)

    Returns:
        Dictionary with performance metrics
    """
    investor_id = ctx.deps.investor_id
    investor = await sync_to_async(Investor.objects.get)(id=investor_id)

    # Get transaction history for the period
    start_date = datetime.now() - timedelta(days=period_days)

    def get_transactions_data():
        transaction_queryset = Transaction.objects.filter(
            investor=investor,
            timestamp__gte=start_date,
        )

        # Calculate stats - using F expressions to avoid N+1 issues
        buy_transactions = transaction_queryset.filter(is_buy=True)
        sell_transactions = transaction_queryset.filter(is_buy=False)

        # Properly calculate total values
        buy_values = list(buy_transactions.values_list("volume", "price"))
        total_buy_value = (
            sum(vol * price for vol, price in buy_values) if buy_values else Decimal(0)
        )

        sell_values = list(sell_transactions.values_list("volume", "price"))
        total_sell_value = (
            sum(vol * price for vol, price in sell_values)
            if sell_values
            else Decimal(0)
        )

        return {
            "transaction_count": transaction_queryset.count(),
            "buy_count": buy_transactions.count(),
            "sell_count": sell_transactions.count(),
            "total_buy_value": total_buy_value,
            "total_sell_value": total_sell_value,
        }

    data = await sync_to_async(get_transactions_data)()

    # Calculate realized gain/loss
    realized_gain_loss = data["total_sell_value"] - data["total_buy_value"]

    return {
        "status": "success",
        "period_days": period_days,
        "transaction_count": data["transaction_count"],
        "buy_count": data["buy_count"],
        "sell_count": data["sell_count"],
        "total_buy_value": str(data["total_buy_value"]),
        "total_sell_value": str(data["total_sell_value"]),
        "realized_gain_loss": str(realized_gain_loss),
        "realized_return_percent": str(
            (realized_gain_loss / data["total_buy_value"] * 100)
            if data["total_buy_value"] > 0
            else Decimal(0)
        ),
    }
