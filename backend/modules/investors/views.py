import logging
import random
from datetime import datetime, timedelta, timezone

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
        investor_tickers = list(
            Instrument.objects.filter(
                id__in=Transaction.objects.filter(investor=investor)
                .values_list("ticker_id", flat=True)
                .distinct()
            )
        )

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
        responses={200: AccountValueSnapshotDailySerializer},
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
        first_transaction_timestamp = (
            Transaction.objects.filter(investor=investor)
            .order_by("timestamp")
            .first()
            .timestamp
        )
        today = get_local_datetime()
        current_timestamp = today - timedelta(minutes=30)
        investor_tickers = list(
            Instrument.objects.filter(
                id__in=Transaction.objects.filter(investor=investor)
                .values_list("ticker_id", flat=True)
                .distinct()
            )
        )

        investor_stats_service = InvestorStatsService()
        total_value = investor_stats_service.get_total_value(investor=investor)

        stats_service = TransactionStatsService()
        stats_today = stats_service.get_stats(
            investor=investor,
            tickers=investor_tickers,
            start_datetime=first_transaction_timestamp,
            end_datetime=current_timestamp,
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

        today = get_local_datetime()
        end_datetime = today - timedelta(minutes=30)
        start_datetime = end_datetime - timedelta(days=365)
        investor_tickers = list(
            Instrument.objects.filter(
                id__in=Transaction.objects.filter(investor=investor)
                .values_list("ticker_id", flat=True)
                .distinct()
            )
        )

        stats_service = TransactionStatsService()
        stats_today = stats_service.get_stats(
            investor=investor,
            tickers=investor_tickers,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )
        total_return_this_year = sum(stat.gain for stat in stats_today)

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

        data = [
            {
                "name": asset_allocation.asset.ticker.name,
                "symbol": asset_allocation.asset.ticker.ticker,
                "logo": asset_allocation.asset.ticker.logo,
                "icon": asset_allocation.asset.ticker.icon,
                "volume": round(asset_allocation.asset.volume, 5),
                "value": round(asset_allocation.total_value, 2),
                "profit": 50.12,  # tmp mocked
                "profit_percentage": 230.88,  # tmp mocked
            }
            for asset_allocation in asset_allocations
        ]
        # data = [
        #     {
        #         **asset_allocation,
        #         "profit_percentage": round(
        #             (
        #                 asset_allocation["profit"]
        #                 / (asset_allocation["value"] - asset_allocation["profit"])
        #             )
        #             * 100,
        #             2,
        #         )
        #         if (asset_allocation["value"] - asset_allocation["profit"]) != 0
        #         else 0,
        #     }
        #     for asset_allocation in data
        # ]

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
        end_datetime = today - timedelta(minutes=30)
        start_datetime = end_datetime - timedelta(days=365)  # tmp last year
        investor_tickers = list(
            Instrument.objects.filter(
                id__in=Transaction.objects.filter(investor=investor)
                .values_list("ticker_id", flat=True)
                .distinct()
            )
        )

        stats_service = TransactionStatsService()
        stats = stats_service.get_stats(
            investor=investor,
            tickers=investor_tickers,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )

        response = {
            "total_trades": sum(
                s.buy_transactions + s.sell_transactions for s in stats
            ),
            "buys": sum(s.buy_transactions for s in stats),
            "sells": sum(s.sell_transactions for s in stats),
            "avg_gain": 0,  # tmp mocked
            "avg_loss": 0,  # tmp mocked
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

        today = get_local_datetime()
        end_datetime = today - timedelta(minutes=30)
        start_datetime = end_datetime - timedelta(days=365)  # tmp last year
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
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )

        data = [
            {
                "symbol": s.ticker,
                "no_trades": s.buy_transactions + s.sell_transactions,
                "buys": s.buy_transactions,
                "sells": s.sell_transactions,
                "avg_gain": 0,  # tmp mocked
                "avg_loss": 0,  # tmp mocked
                "total_return": s.gain,
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
        position_type = request.query_params.get("type", "both")
        ticker = request.query_params.get("ticker", None)

        # Use user ID as seed for consistent data per user
        random.seed(hash(self.request.user.id))

        # Mock stock symbols
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "NFLX", "META"]

        # Filter by ticker if provided
        if ticker:
            symbols = [ticker] if ticker in symbols else []

        positions = []
        for symbol in symbols:
            # Generate random transaction history for this symbol
            transaction_count = random.randint(1, 6)
            history = []

            for _ in range(transaction_count):
                transaction_type = random.choice(["BUY", "SELL"])

                days_ago = random.randint(1, 1000)
                past_dt = datetime.now(timezone.utc) - timedelta(days=days_ago)

                history_entry = {
                    "date": past_dt.isoformat(),
                    "type": transaction_type,
                    "quantity": random.randint(1, 10),
                    "share_price": round(random.uniform(50, 1000), 2),
                    "acquisition_price": (
                        round(random.uniform(50, 1000), 2)
                        if transaction_type == "BUY"
                        else None
                    ),
                    "market_value": round(random.uniform(100, 10000), 2),
                    "gain_loss": round(random.uniform(-500, 500), 2),
                    "gain_loss_pct": round(random.uniform(-50, 50), 2),
                }
                history.append(history_entry)

            # Sort history by date (newest first)
            history.sort(key=lambda x: x["date"], reverse=True)

            # Calculate position totals
            total_quantity = sum(
                h["quantity"] if h["type"] == "BUY" else -h["quantity"] for h in history
            )

            # Only include positions based on type filter
            if position_type == "open" and total_quantity <= 0:
                continue
            if position_type == "closed" and total_quantity > 0:
                continue

            position = {
                "name": symbol,
                "quantity": max(0, total_quantity),
                "market_value": round(random.uniform(1000, 50000), 2),
                "gain_loss": round(random.uniform(-1000, 1000), 2),
                "gain_loss_pct": round(random.uniform(-25, 25), 2),
                "history": history,
            }
            positions.append(position)

        # Return as array directly (matching frontend expectation)
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
