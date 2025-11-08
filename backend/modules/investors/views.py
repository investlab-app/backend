import logging

from django.db import transaction
from django.db.models.expressions import OuterRef, Subquery
from django.db.models.functions.datetime import TruncDate
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response

from modules.instruments.models import Instrument
from modules.investors.models import AccountValueSnapshot, Asset, Investor
from modules.investors.serializers import (
    AccountValueSnapshotDailySerializer,
    AssetSerializer,
    DepositMoneySerializer,
    InvestorSerializer,
    NotificationHistorySerializer,
    WatchedTickerSerializer,
    WatchedTickersTickerSerializer,
)

logger = logging.getLogger(__name__)


class InvestorDetailView(generics.RetrieveUpdateAPIView):
    queryset = Investor.objects.all()
    serializer_class = InvestorSerializer
    http_method_names = ["get", "patch"]
    lookup_field = "clerk_id"


class CurrentInvestorView(generics.RetrieveUpdateAPIView):
    """
    Get the current authenticated user's investor profile.
    """

    serializer_class = InvestorSerializer
    queryset = Investor.objects.all()
    http_method_names = ["get", "patch"]

    def get_object(self):
        """Retrieve the current authenticated user's investor profile."""
        investor, _ = Investor.objects.get_or_create(clerk_id=self.request.user.id)
        return investor

    @extend_schema(
        responses={200: InvestorSerializer},
        summary="Get current investor",
        description="Get the investor profile for the currently authenticated user.",
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)

    @extend_schema(
        request=InvestorSerializer,
        responses={200: InvestorSerializer},
        summary="Update current investor",
        description="Update the investor profile for the currently authenticated user.",
    )
    def patch(self, request: Request, *args, **kwargs) -> Response:
        return super().patch(request, *args, **kwargs)


class AssetListView(generics.ListAPIView):
    serializer_class = AssetSerializer

    def get_queryset(self):
        investor = Investor.objects.get(clerk_id=self.request.user.id)
        return Asset.objects.filter(investor=investor)


class WatchedTickersListView(generics.ListAPIView):
    serializer_class = WatchedTickerSerializer
    pagination_class = None

    def get_queryset(self):
        investor = Investor.objects.get(clerk_id=self.request.user.id)
        return investor.watching_instruments.all()


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


class WatchedTickersTickerView(generics.GenericAPIView):
    serializer_class = WatchedTickersTickerSerializer

    def patch(self, request: Request, instrument_id: str) -> Response:
        investor, _ = Investor.objects.get_or_create(clerk_id=request.user.id)
        instrument = get_object_or_404(Instrument, id=instrument_id)

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        should_watch = serializer.validated_data["is_watched"]

        with transaction.atomic():
            if should_watch:
                investor.watching_instruments.add(instrument)
            else:
                investor.watching_instruments.remove(instrument)

        return Response(
            {
                "instrument_id": str(instrument.id),
                "is_watched": should_watch,
            },
            status=status.HTTP_200_OK,
        )


class DepositMoneyView(generics.GenericAPIView):
    serializer_class = DepositMoneySerializer

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        amount = serializer.validated_data["amount"]

        user_clerk_id = request.user.id
        investor, _ = Investor.objects.get_or_create(clerk_id=user_clerk_id)
        investor.balance += amount
        investor.save()

        logger.info("Deposited %s to investor with clerk_id %s", amount, user_clerk_id)

        return Response({"status": "success", "amount": str(amount)}, status=200)


class NotificationHistoryView(generics.ListAPIView):
    serializer_class = NotificationHistorySerializer
    pagination_class = None

    def get_queryset(self):
        investor = Investor.objects.get(clerk_id=self.request.user.id)
        return investor.notifications.order_by("-sent_at")

    def list(self, request: Request, *args, **kwargs) -> Response:
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
