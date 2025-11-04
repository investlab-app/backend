# import logging
# from datetime import datetime, timedelta
# from decimal import Decimal

# from asgiref.sync import sync_to_async
# from pydantic_ai.tools import Tool

# from modules.investors.models import Asset, Investor
# from modules.prices.repositories import PolygonPricesRepository
# from modules.transactions.models import Transaction

# logger = logging.getLogger(__name__)


# def create_portfolio_tool() -> Tool:
#     """Get current portfolio positions for the investor."""

#     async def get_portfolio(investor_id: str) -> dict:
#         """
#         Get current portfolio positions including holdings, quantities, and
#         current values.

#         Args:
#             investor_id: The investor's UUID as string

#         Returns:
#             Dictionary with portfolio summary and positions
#         """
#         try:
#             logger.info(f"Fetching portfolio for investor {investor_id}")

#             def fetch_portfolio_data():
#                 investor = Investor.objects.get(id=investor_id)
#                 assets = Asset.objects.filter(investor=investor).select_related(
#                     "ticker"
#                 )

#                 if not assets:
#                     return {
#                         "status": "success",
#                         "balance": str(investor.balance),
#                         "positions": [],
#                         "total_value": str(investor.balance),
#                     }

#                 # Get current prices
#                 tickers = [a.ticker.ticker.upper() for a in assets]
#                 prices_repo = PolygonPricesRepository()
#                 prices = prices_repo.get_prices_map(tickers)

#                 if prices is None:
#                     return {
#                         "status": "error",
#                         "message": "Failed to fetch current prices",
#                     }

#                 positions = []
#                 total_holdings_value = Decimal("0")

#                 for asset in assets:
#                     ticker_upper = asset.ticker.ticker.upper()
#                     current_price = prices[ticker_upper].current_price
#                     position_value = asset.volume * current_price
#                     total_holdings_value += position_value

#                     positions.append(
#                         {
#                             "ticker": asset.ticker.ticker,
#                             "quantity": str(asset.volume),
#                             "current_price": str(current_price),
#                             "position_value": str(position_value),
#                             "percentage_of_portfolio": None,  # Will calculate after
#                         }
#                     )

#                 total_portfolio_value = investor.balance + total_holdings_value

#                 # Calculate percentages
#                 for position in positions:
#                     value = Decimal(position["position_value"])
#                     pct = (
#                         (value / total_portfolio_value * 100)
#                         if total_portfolio_value > 0
#                         else Decimal("0")
#                     )
#                     position["percentage_of_portfolio"] = str(pct)

#                 return {
#                     "status": "success",
#                     "balance": str(investor.balance),
#                     "cash_percentage": str(
#                         (investor.balance / total_portfolio_value * 100)
#                         if total_portfolio_value > 0
#                         else Decimal("0")
#                     ),
#                     "holdings_value": str(total_holdings_value),
#                     "total_value": str(total_portfolio_value),
#                     "positions": positions,
#                 }

#             result = await sync_to_async(fetch_portfolio_data)()
#             if result.get("status") == "success":
#                 logger.info(
#                     f"Successfully fetched portfolio for investor {investor_id}"
#                 )
#             return result
#         except Investor.DoesNotExist:
#             logger.warning(f"Investor not found: {investor_id}")
#             return {"status": "error", "message": "Investor not found"}
#         except Exception as e:
#             logger.exception(
#                 f"Error fetching portfolio for investor {investor_id}: {e}"
#             )
#             return {"status": "error", "message": str(e)}

#     return Tool(
#         get_portfolio,
#         description="Get the investor's current portfolio positions, cash balance, and total portfolio value",
#     )


# def create_transactions_tool() -> Tool:
#     """Get transaction history for the investor."""

#     async def get_transactions(investor_id: str, limit: int = 20) -> dict:
#         """
#         Get recent transactions (trades) for the investor.

#         Args:
#             investor_id: The investor's UUID as string
#             limit: Maximum number of transactions to return (default 20)

#         Returns:
#             Dictionary with transaction history
#         """
#         try:
#             logger.info(
#                 f"Fetching transactions for investor {investor_id}, limit={limit}"
#             )

#             def fetch_transaction_history():
#                 investor = Investor.objects.get(id=investor_id)
#                 transaction_queryset = (
#                     Transaction.objects.filter(investor=investor)
#                     .select_related("ticker")
#                     .order_by("-timestamp")[:limit]
#                 )

#                 transaction_list = [
#                     {
#                         "id": str(t.id),
#                         "ticker": t.ticker.ticker,
#                         "type": "BUY" if t.is_buy else "SELL",
#                         "quantity": str(t.volume),
#                         "price": str(t.price),
#                         "total_value": str(t.volume * t.price),
#                         "timestamp": t.timestamp.isoformat(),
#                     }
#                     for t in transaction_queryset
#                 ]

#                 return {
#                     "status": "success",
#                     "count": len(transaction_list),
#                     "transactions": transaction_list,
#                 }

#             result = await sync_to_async(fetch_transaction_history)()
#             logger.info(
#                 f"Successfully fetched {result['count']} transactions for investor {investor_id}"
#             )
#             return result
#         except Investor.DoesNotExist:
#             logger.warning(f"Investor not found: {investor_id}")
#             return {"status": "error", "message": "Investor not found"}
#         except Exception as e:
#             logger.exception(
#                 f"Error fetching transactions for investor {investor_id}: {e}"
#             )
#             return {"status": "error", "message": str(e)}

#     return Tool(
#         get_transactions,
#         description="Get recent transaction history for the investor's trades",
#     )


# def create_performance_tool() -> Tool:
#     """Get portfolio performance metrics."""

#     async def get_portfolio_performance(
#         investor_id: str, period_days: int = 30
#     ) -> dict:
#         """
#         Get portfolio performance metrics for a given period.

#         Args:
#             investor_id: The investor's UUID as string
#             period_days: Number of days to look back (default 30)

#         Returns:
#             Dictionary with performance metrics
#         """
#         try:
#             logger.info(
#                 f"Fetching performance metrics for investor {investor_id}, period={period_days}d"
#             )

#             def fetch_performance_metrics():
#                 investor = Investor.objects.get(id=investor_id)

#                 # Get transaction history for the period
#                 start_date = datetime.now() - timedelta(days=period_days)
#                 transaction_queryset = Transaction.objects.filter(
#                     investor=investor,
#                     timestamp__gte=start_date,
#                 )

#                 # Calculate stats - using F expressions to avoid N+1 issues
#                 buy_transactions = transaction_queryset.filter(is_buy=True)
#                 sell_transactions = transaction_queryset.filter(is_buy=False)

#                 # Properly calculate total values
#                 buy_values = buy_transactions.values_list("volume", "price")
#                 total_buy_value = (
#                     sum(vol * price for vol, price in buy_values)
#                     if buy_values
#                     else Decimal("0")
#                 )

#                 sell_values = sell_transactions.values_list("volume", "price")
#                 total_sell_value = (
#                     sum(vol * price for vol, price in sell_values)
#                     if sell_values
#                     else Decimal("0")
#                 )

#                 # Calculate realized gain/loss
#                 realized_gain_loss = total_sell_value - total_buy_value

#                 transaction_count = transaction_queryset.count()
#                 buy_count = buy_transactions.count()
#                 sell_count = sell_transactions.count()

#                 return {
#                     "status": "success",
#                     "period_days": period_days,
#                     "transaction_count": transaction_count,
#                     "buy_count": buy_count,
#                     "sell_count": sell_count,
#                     "total_buy_value": str(total_buy_value),
#                     "total_sell_value": str(total_sell_value),
#                     "realized_gain_loss": str(realized_gain_loss),
#                     "realized_return_percent": str(
#                         (realized_gain_loss / total_buy_value * 100)
#                         if total_buy_value > 0
#                         else Decimal("0")
#                     ),
#                 }

#             result = await sync_to_async(fetch_performance_metrics)()
#             logger.info(
#                 f"Successfully fetched performance metrics for investor {investor_id}"
#             )
#             return result
#         except Investor.DoesNotExist:
#             logger.warning(f"Investor not found: {investor_id}")
#             return {"status": "error", "message": "Investor not found"}
#         except Exception as e:
#             logger.exception(
#                 f"Error fetching performance metrics for investor {investor_id}: {e}"
#             )
#             return {"status": "error", "message": str(e)}

#     return Tool(
#         get_portfolio_performance,
#         description="Get portfolio performance metrics for a specified period",
#     )
