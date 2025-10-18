import logging
from datetime import timedelta

from django.db.models.aggregates import Count
from django.db.models.expressions import OuterRef, Subquery
from django.db.models.functions.datetime import TruncDate
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from modules.core.utils import get_local_datetime
from modules.instruments.models import Instrument
from modules.investors.models import AccountValueSnapshot, Asset, Investor
from modules.investors.serializers import (
    AccountValueSnapshotDailySerializer,
    AssetAllocationSerializer,
    AssetSerializer,
    CurrentAccountValueSerializer,
    InvestorListQueryParams,
    InvestorSerializer,
    InvestorStatsSerializer,
    InvestorUpdateSerializer,
    MostTradedItemSerializer,
    OwnedShareSerializer,
    PositionSerializer,
    TradingOverviewSerializer,
    TransactionHistoryQueryParams,
)
from modules.investors.services import InvestorStatsService
from modules.transactions.models import Transaction
from modules.transactions.services import TransactionStatsService

logger = logging.getLogger(__name__)


def get_investor_tickers(investor: Investor):
    return list(
        Instrument.objects.filter(
            id__in=Transaction.objects.filter(investor=investor)
            .values_list("ticker_id", flat=True)
            .distinct()
        )
    )


class InvestorListView(generics.ListAPIView):
    """
    List all investors.
    """

    queryset = Investor.objects.prefetch_related("watching_instruments")
    serializer_class = InvestorSerializer

    def get_serializer_class(self):
        return InvestorSerializer

    @extend_schema(
        parameters=[InvestorListQueryParams],
        responses={200: InvestorSerializer(many=True)},
        summary="List investors",
        description="Get a paginated list of investors with optional search filtering.",
    )
    def get(self, request: Request) -> Response:
        return super().get(request)


class InvestorDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve or update an investor.
    """

    queryset = Investor.objects.prefetch_related("watching_instruments")
    serializer_class = InvestorSerializer
    lookup_field = "clerk_id"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return InvestorUpdateSerializer
        return InvestorSerializer

    @extend_schema(
        responses={200: InvestorSerializer},
        summary="Get investor",
        description="Retrieve a specific investor by ID.",
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        request=InvestorUpdateSerializer,
        responses={200: InvestorSerializer},
        summary="Update investor",
        description="Update an investor's information.",
    )
    def put(self, request: Request, *args, **kwargs) -> Response:
        return super().put(request, *args, **kwargs)

    @extend_schema(
        request=InvestorUpdateSerializer,
        responses={200: InvestorSerializer},
        summary="Partially update investor",
        description="Partially update an investor's information.",
    )
    def patch(self, request: Request, *args, **kwargs) -> Response:
        return super().patch(request, *args, **kwargs)


class CurrentInvestorView(generics.RetrieveAPIView):
    """
    Get the current authenticated user's investor profile.
    """

    serializer_class = InvestorSerializer

    def get_object(self):
        return Investor.objects.prefetch_related("watching_instruments").get(
            clerk_id=self.request.user.id
        )

    @extend_schema(
        responses={200: InvestorSerializer},
        summary="Get current investor",
        description="Get the investor profile for the currently authenticated user.",
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)


class InvestorStatsView(generics.RetrieveAPIView):
    """
    Get investor statistics for the current authenticated user.
    """

    serializer_class = InvestorStatsSerializer

    def retrieve(self, request, *args, **kwargs):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)

        today = get_local_datetime()
        end_datetime = today - timedelta(minutes=30)
        start_datetime = end_datetime - timedelta(days=1)
        investor_tickers = get_investor_tickers(investor)

        stats_service = TransactionStatsService()
        stats_today = stats_service.get_stats(
            investor=investor,
            tickers=investor_tickers,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )
        todays_return = sum(stat.gain for stat in stats_today)

        stats_total = stats_service.get_stats(
            investor=investor,
            tickers=investor_tickers,
        )
        total_return = sum(stat.gain for stat in stats_total)
        invested = sum(stat.total_buy_price for stat in stats_total)

        investor_stats_service = InvestorStatsService()
        total_value = investor_stats_service.get_total_value(investor=investor)

        stats_data = {
            "todays_return": todays_return,
            "total_return": total_return,
            "invested": invested,
            "total_value": total_value,
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


class AccountValueOverTimeView(generics.ListAPIView):
    """
    Get account value over time data for the current authenticated user.
    """

    serializer_class = AccountValueSnapshotDailySerializer
    pagination_class = None

    def get_queryset(self):
        """
        The earliest snapshot for each day is selected to represent that day's value.
        """
        investor_id = self.request.user.id

        earliest_snapshots = (
            AccountValueSnapshot.objects.filter(
                investor__clerk_id=investor_id,
                timestamp__date=OuterRef("day"),
            )
            .order_by("timestamp")
            .values("id")[:1]
        )

        qs = (
            AccountValueSnapshot.objects.annotate(day=TruncDate("timestamp"))
            .filter(id__in=Subquery(earliest_snapshots))
            .order_by("-timestamp")
        )

        return qs

    @extend_schema(
        responses={200: AccountValueSnapshotDailySerializer(many=True)},
        summary="Get account value over time",
        description=(
            "Get account value over time data for the currently authenticated user."
        ),
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
        investor_tickers = get_investor_tickers(investor)

        investor_stats_service = InvestorStatsService()
        total_value = investor_stats_service.get_total_value(investor=investor)

        stats_service = TransactionStatsService()
        stats_today = stats_service.get_stats(
            investor=investor,
            tickers=investor_tickers,
        )
        total_gain = sum(stat.gain for stat in stats_today)

        response = {
            "total_account_value": round(total_value, 2),
            "gain": round(total_gain, 2),
            "gain_percent": 0,  # tmp mocked
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
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        investor_tickers = get_investor_tickers(investor)

        stats_service = TransactionStatsService()
        stats_last_year = stats_service.get_stats(
            investor=investor,
            tickers=investor_tickers,
        )
        total_return_this_year = sum(stat.gain for stat in stats_last_year)

        is_service = InvestorStatsService()
        total_value = is_service.get_total_value(investor=investor)
        asset_allocations = is_service.get_asset_allocation(investor=investor)

        response_data = {
            "total_value": round(total_value, 2),
            "total_return_this_year": round(total_return_this_year, 2),
            "allocations": [
                {
                    "instrument_name": allocation.asset.ticker.name,
                    "instrument_ticker": allocation.asset.ticker.ticker,
                    "instrument_logo": allocation.asset.ticker.logo,
                    "instrument_icon": allocation.asset.ticker.icon,
                    "value": round(allocation.total_value, 2),
                    "percentage": round(allocation.percentage, 2),
                }
                for allocation in asset_allocations
            ],
        }

        serializer = self.get_serializer(response_data)
        return Response(serializer.data)

    @extend_schema(
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

    def retrieve(self, request, *args, **kwargs):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        is_service = InvestorStatsService()
        asset_allocations = is_service.get_asset_allocation(investor=investor)
        tickers = [aa.asset.ticker for aa in asset_allocations]
        tr_stats_service = TransactionStatsService()
        stats = tr_stats_service.get_stats(
            investor=investor,
            tickers=tickers,
        )
        stats_map = {s.ticker: s for s in stats}

        data = [
            {
                "name": asset_allocation.asset.ticker.name,
                "symbol": asset_allocation.asset.ticker.ticker,
                "logo": asset_allocation.asset.ticker.logo,
                "icon": asset_allocation.asset.ticker.icon,
                "volume": round(asset_allocation.asset.volume, 5),
                "value": round(asset_allocation.total_value, 2),
                "profit": stats_map[str(asset_allocation.asset.ticker.ticker)].gain,
                "profit_percentage": stats_map[str(asset_allocation.asset.ticker.ticker)].gain_percentage,
            }
            for asset_allocation in asset_allocations
        ]

        serializer = self.get_serializer(data, many=True)
        return Response(serializer.data)

    @extend_schema(
        responses={200: OwnedShareSerializer},
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

        today = get_local_datetime()
        investor_tickers = get_investor_tickers(investor)

        stats_service = TransactionStatsService()
        stats = stats_service.get_stats(
            investor=investor,
            tickers=investor_tickers,
        )

        response = {
            "total_trades": sum(
                s.buy_transactions + s.sell_transactions for s in stats
            ),
            "buys": sum(s.buy_transactions for s in stats),
            "sells": sum(s.sell_transactions for s in stats),
            "total_return": round(sum(s.gain for s in stats), 2),
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

        stats_service = TransactionStatsService()
        stats = stats_service.get_stats(
            investor=investor,
            tickers=instruments,
        )

        data = [
            {
                "symbol": s.ticker,
                "no_trades": s.buy_transactions + s.sell_transactions,
                "buys": s.buy_transactions,
                "sells": s.sell_transactions,
                "total_return": s.gain,
                "percentage_return": s.gain_percentage,
            }
            for s in stats
        ]

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

    pagination_class = None

    def retrieve(self, request, *args, **kwargs):
        parameters = TransactionHistoryQueryParams(data=request.query_params)
        parameters.is_valid(raise_exception=True)
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        position_type = parameters.validated_data.get("type", "both")
        tickers = parameters.validated_data.get("tickers", [])
        if not tickers:
            tickers = get_investor_tickers(investor)

        transactions = Transaction.objects.filter(investor=investor).select_related(
            "ticker"
        )
        asset_allocations = InvestorStatsService().get_asset_allocation(investor)
        asset_allocations_map = {
            aa.asset.ticker.ticker.upper(): aa for aa in asset_allocations
        }

        stats_service = TransactionStatsService()
        stats = stats_service.get_stats(
            investor=investor,
            tickers=tickers,
        )
        stats_map = {s.ticker: s for s in stats}

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

            position = {
                "name": ticker_symbol,
                "quantity": quantity,
                "market_value": round(market_value, 2),
                "gain_loss": round(stats_map[ticker_symbol].gain, 2),
                "gain_loss_pct": round(stats_map[ticker_symbol].gain, 2),  # tmp mocked
                "history": history,
            }
            positions.append(position)

        serializer = PositionSerializer(positions, many=True)
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


class AssetListView(generics.ListAPIView):
    serializer_class = AssetSerializer

    def get_queryset(self):
        investor = Investor.objects.get(clerk_id=self.request.user.id)
        return Asset.objects.filter(investor=investor)
