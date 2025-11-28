import logging
from datetime import timedelta
from decimal import Decimal

from django.db.models.aggregates import Count
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from modules.core.utils import get_local_datetime
from modules.instruments.models import Instrument
from modules.investors.models import Investor
from modules.investors.services import InvestorStatsService
from modules.statistics.serializers import (
    AssetAllocationQueryParams,
    AssetAllocationSerializer,
    CurrentAccountValueSerializer,
    InvestorStatsSerializer,
    MostTradedItemSerializer,
    OwnedShareSerializer,
    PositionSerializer,
    TradingOverviewSerializer,
    TransactionHistoryQueryParams,
)
from modules.statistics.services import MultiInstrumentsTransactionStatsService
from modules.statistics.utils import get_investor_tickers
from modules.transactions.models import Transaction

logger = logging.getLogger(__name__)


class InvestorStatsView(generics.RetrieveAPIView):
    """
    Get investor statistics for the current authenticated user.
    """

    serializer_class = InvestorStatsSerializer

    def retrieve(self, request, *args, **kwargs):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)

        today = get_local_datetime()
        start_datetime = today - timedelta(days=1)

        stats_service = MultiInstrumentsTransactionStatsService(investor=investor)
        stats_today = stats_service.compute_stats(start=start_datetime)
        todays_gain = stats_today.sum_attribute("total_gain")

        stats_total = stats_service.compute_stats()
        total_gain = stats_total.sum_attribute("total_gain")
        invested = stats_total.sum_attribute("total_buy_cost")

        investor_stats_service = InvestorStatsService()
        total_value = investor_stats_service.get_total_value(investor=investor)

        stats_data = {
            "todays_gain": round(todays_gain, 2),
            "total_gain": round(total_gain, 2),
            "invested": round(invested, 2),
            "total_value": round(total_value, 2),
        }

        serializer = self.get_serializer(stats_data)
        return Response(serializer.data)

    @extend_schema(
        responses={200: InvestorStatsSerializer},
        summary="Get investor stats",
        description="Get investor statistics for the currently authenticated user.",
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)


class CurrentAccountValueView(generics.RetrieveAPIView):
    """
    Get the current account value for the authenticated user.
    """

    serializer_class = CurrentAccountValueSerializer

    def retrieve(self, request, *args, **kwargs):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)

        investor_stats_service = InvestorStatsService()
        total_value = investor_stats_service.get_total_value(investor=investor)

        stats_service = MultiInstrumentsTransactionStatsService(investor=investor)
        stats_today = stats_service.compute_stats()
        total_gain = stats_today.sum_attribute("total_gain")
        total_gain_pct = stats_today.calculate_total_gain_pct()
        if total_gain_pct is not None and total_gain_pct > 9999.99:
            total_gain_pct = Decimal("9999.99")

        response = {
            "total_account_value": round(total_value, 2),
            "gain": round(total_gain, 2),
            "gain_percentage": round(total_gain_pct, 2)
            if total_gain_pct is not None
            else None,
        }

        serializer = self.get_serializer(response)
        return Response(serializer.data)

    @extend_schema(
        responses={200: CurrentAccountValueSerializer},
        summary="Get current account value",
        description=(
            "Get the current account value as well as gain and percent gain "
            "for the authenticated user."
        ),
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)


class AssetAllocationView(generics.RetrieveAPIView):
    """
    Get asset allocation data for the current authenticated user.
    """

    serializer_class = AssetAllocationSerializer

    def retrieve(self, request, *args, **kwargs):
        parameters = AssetAllocationQueryParams(data=request.query_params)
        parameters.is_valid(raise_exception=True)
        instruments_number = parameters.validated_data["instruments_number"]
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)

        today = get_local_datetime()
        year_ago = today - timedelta(days=365)
        stats_service = MultiInstrumentsTransactionStatsService(investor=investor)
        stats_last_year = stats_service.compute_stats(start=year_ago)
        total_gain_this_year = stats_last_year.sum_attribute("total_gain")

        is_service = InvestorStatsService()
        total_value = is_service.get_total_assets_value(investor=investor)
        asset_allocations = is_service.get_asset_allocation(investor=investor)
        asset_allocations = sorted(
            asset_allocations, key=lambda x: x.percentage, reverse=True
        )
        main_allocations = asset_allocations[:instruments_number]
        rest_allocations = asset_allocations[instruments_number:]

        response_data = {
            "total_value": round(total_value, 2),
            "total_gain_this_year": round(total_gain_this_year, 2),
            "allocations": [
                {
                    "instrument_name": allocation.asset.ticker.name,
                    "instrument_ticker": allocation.asset.ticker.ticker,
                    "instrument_logo": (
                        logo if (logo := allocation.asset.ticker.logo) else None
                    ),
                    "instrument_icon": (
                        icon if (icon := allocation.asset.ticker.icon) else None
                    ),
                    "value": round(allocation.total_value, 2),
                    "percentage": round(allocation.percentage, 2),
                }
                for allocation in main_allocations
            ],
        }

        # Add "Other" allocation if there are remaining allocations
        if rest_allocations:
            response_data["allocations"].append(
                {
                    "instrument_name": "Other",
                    "instrument_ticker": "OTHER",
                    "instrument_logo": None,
                    "instrument_icon": None,
                    "value": round(
                        sum(
                            (a.total_value for a in rest_allocations),
                            start=Decimal(0),
                        ),
                        2,
                    ),
                    "percentage": round(
                        sum(a.percentage for a in rest_allocations),
                        2,
                    ),
                }
            )

        serializer = self.get_serializer(response_data)
        return Response(serializer.data)

    @extend_schema(
        parameters=[AssetAllocationQueryParams],
        responses={200: AssetAllocationSerializer},
        summary="Get asset allocation",
        description="Get asset allocation data for the currently authenticated user.",
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)


class OwnedSharesView(generics.RetrieveAPIView):
    """
    Get owned shares data for the current authenticated user.
    """

    serializer_class = OwnedShareSerializer
    pagination_class = None

    def retrieve(self, request, *args, **kwargs):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        is_service = InvestorStatsService()
        asset_allocations = is_service.get_asset_allocation(investor=investor)
        instruments = [aa.asset.ticker for aa in asset_allocations]
        tr_stats_service = MultiInstrumentsTransactionStatsService(
            investor=investor, instruments=instruments
        )
        stats_map = tr_stats_service.compute_stats()

        data = []
        for asset_allocation in asset_allocations:
            instrument = asset_allocation.asset.ticker
            ticker_key = str(instrument.ticker)
            stat = stats_map[ticker_key]

            data.append(
                {
                    "name": instrument.name,
                    "symbol": instrument.ticker,
                    "logo": instrument.logo,
                    "icon": instrument.icon,
                    "volume": round(asset_allocation.asset.volume, 5),
                    "value": round(asset_allocation.total_value, 2),
                    "gain": round(stat.total_gain, 2),
                    "gain_percentage": round(Decimal(stat.total_gain_pct), 2)
                    if stat.total_gain_pct is not None
                    else None,
                }
            )

        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)

    @extend_schema(
        responses={200: OwnedShareSerializer(many=True)},
        summary="Get owned shares",
        description="Get owned shares data for the currently authenticated user.",
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)


class TradingOverviewView(generics.RetrieveAPIView):
    """
    Get the trading statistics for the current investor.
    """

    serializer_class = TradingOverviewSerializer

    def retrieve(self, request, *args, **kwargs):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)

        stats_service = MultiInstrumentsTransactionStatsService(investor=investor)
        stats = stats_service.compute_stats()
        total_gain = stats.sum_attribute("total_gain")

        investor_tr = Transaction.objects.filter(investor=investor)
        buy_tr = investor_tr.filter(is_buy=True).count()
        sell_tr = investor_tr.filter(is_buy=False).count()

        response = {
            "total_trades": buy_tr + sell_tr,
            "buys": buy_tr,
            "sells": sell_tr,
            "total_gain": round(total_gain, 2),
        }

        serializer = self.get_serializer(response)
        return Response(serializer.data)

    @extend_schema(
        responses={200: TradingOverviewSerializer},
        summary="Get trading performance overview",
        description=(
            "Returns total trades, number of buys/sells, average gain/loss, "
            "and total return for the current investor."
        ),
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)


class MostTradedOverviewView(generics.RetrieveAPIView):
    """
    Get the statistics for the most traded instruments of the current investor.
    """

    serializer_class = MostTradedItemSerializer
    pagination_class = None

    def retrieve(self, request, *args, **kwargs):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)

        instruments_by_transaction_count = (
            Transaction.objects.filter(investor=investor)
            .values("ticker")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        instrument_ids = [str(i["ticker"]) for i in instruments_by_transaction_count]
        instruments = list(Instrument.objects.filter(id__in=instrument_ids))

        stats_service = MultiInstrumentsTransactionStatsService(
            investor=investor, instruments=instruments
        )
        stats = stats_service.compute_stats()

        transactions = Transaction.objects.filter(investor=investor)

        data = []
        for ticker, stat in stats.items():
            instrument_transactions = transactions.filter(ticker__ticker=ticker)
            buy_transactions_count = instrument_transactions.filter(is_buy=True).count()
            sell_transactions_count = instrument_transactions.filter(
                is_buy=False
            ).count()

            data.append(
                {
                    "symbol": ticker,
                    "no_trades": buy_transactions_count + sell_transactions_count,
                    "buys": buy_transactions_count,
                    "sells": sell_transactions_count,
                    "gain": round(stat.total_gain, 2),
                    "gain_percentage": round(stat.total_gain_pct, 2)
                    if stat.total_gain_pct is not None
                    else None,
                }
            )

        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)

    @extend_schema(
        responses={200: MostTradedItemSerializer(many=True)},
        summary="Get overview about the most traded instruments",
        description=(
            "Returns number of trades, number of buys/sells, avg gain/loss, "
            "and total return from the most frequently traded instruments."
        ),
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)


class TransactionHistoryView(generics.RetrieveAPIView):
    """
    Get transaction history for the current authenticated user.
    """

    serializer_class = PositionSerializer
    pagination_class = None

    def retrieve(self, request, *args, **kwargs):
        parameters = TransactionHistoryQueryParams(data=request.query_params)
        parameters.is_valid(raise_exception=True)
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        position_type = parameters.validated_data.get("type", "both")
        tickers_names = parameters.validated_data.get("tickers", [])
        if tickers_names:
            tickers = Instrument.objects.filter(ticker__in=tickers_names)
        else:
            tickers = get_investor_tickers(investor)

        transactions = Transaction.objects.filter(investor=investor).select_related(
            "ticker"
        )
        asset_allocations = InvestorStatsService().get_asset_allocation(investor)
        asset_allocations_map = {
            aa.asset.ticker.ticker.upper(): aa for aa in asset_allocations
        }

        stats_service = MultiInstrumentsTransactionStatsService(
            investor=investor, instruments=tickers
        )
        stats_map = stats_service.compute_stats()

        positions = []
        for ticker in tickers:
            ticker_symbol = ticker.ticker.upper()

            if position_type == "open" and ticker_symbol not in asset_allocations_map:
                continue

            if position_type == "closed" and ticker_symbol in asset_allocations_map:
                continue

            ticker_transactions = transactions.filter(
                ticker__ticker=ticker_symbol
            ).order_by("-timestamp")

            history = []
            for transaction in ticker_transactions:
                history_entry = {
                    "timestamp": transaction.timestamp,
                    "is_buy": transaction.is_buy,
                    "quantity": transaction.volume,
                    "share_price": round(transaction.price / transaction.volume, 2),
                    "acquisition_price": transaction.price if transaction.is_buy else 0,
                }
                history.append(history_entry)

            quantity, market_value = 0, 0
            if ticker_symbol in asset_allocations_map:
                quantity = asset_allocations_map[ticker_symbol].asset.volume
                market_value = asset_allocations_map[ticker_symbol].total_value

            stat = stats_map[ticker_symbol]
            position = {
                "symbol": ticker_symbol,
                "name": ticker.name,
                "icon": (icon if (icon := ticker.icon) else None),
                "quantity": quantity,
                "market_value": round(market_value, 2),
                "gain": round(stat.total_gain, 2),
                "gain_percentage": round(Decimal(stat.total_gain_pct), 2)
                if stat.total_gain_pct is not None
                else None,
                "history": history,
            }
            positions.append(position)

        serializer = self.get_serializer(positions, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[TransactionHistoryQueryParams],
        responses={200: PositionSerializer(many=True)},
        summary="Get transaction history",
        description=(
            "Get transaction history for the currently authenticated user. "
            "Can filter by position type (open/closed/both) and ticker symbol."
        ),
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)
