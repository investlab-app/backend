import logging

from django.db.models.expressions import OuterRef, Subquery
from django.db.models.functions.datetime import TruncDate
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.request import Request
from rest_framework.response import Response

from modules.investors.models import AccountValueSnapshot, Asset, Investor
from modules.investors.serializers import (
    AccountValueSnapshotDailySerializer,
    AssetSerializer,
    InvestorListQueryParams,
    InvestorSerializer,
    InvestorUpdateSerializer,
)

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


class AssetListView(generics.ListAPIView):
    serializer_class = AssetSerializer

    def get_queryset(self):
        investor = Investor.objects.get(clerk_id=self.request.user.id)
        return Asset.objects.filter(investor=investor)


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
