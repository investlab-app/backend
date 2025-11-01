import logging

from django.db.models.expressions import OuterRef, Subquery
from django.db.models.functions.datetime import TruncDate
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
)
from rest_framework.request import Request
from rest_framework.response import Response

from modules.authentication.clerk_auth import ClerkAuthentication
from modules.instruments.models import Instrument
from modules.investors.models import AccountValueSnapshot, Asset, Investor
from modules.investors.serializers import (
    AccountValueSnapshotDailySerializer,
    AssetSerializer,
    InvestorSerializer,
    InvestorUpdateSerializer,
    LanguageUpdateSerializer,
    ToggleWatchedInstrumentSerializer,
)

logger = logging.getLogger(__name__)


class InvestorDetailView(generics.RetrieveUpdateAPIView):
    queryset = Investor.objects.all()
    serializer_class = InvestorSerializer
    lookup_field = "clerk_id"

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return InvestorUpdateSerializer
        return InvestorSerializer


class CurrentInvestorView(generics.RetrieveAPIView):
    """
    Get the current authenticated user's investor profile.
    """

    serializer_class = InvestorSerializer
    queryset = Investor.objects.all()

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


class LanguageUpdateView(generics.CreateAPIView):
    serializer_class = LanguageUpdateSerializer

    def post(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        language = serializer.validated_data["language"]

        user_clerk_id = request.user.id

        investor, _ = Investor.objects.update_or_create(
            clerk_id=user_clerk_id, defaults={"language": language}
        )

        response_serializer = self.get_serializer({"language": investor.language})
        return Response(response_serializer.data, status=200)


@extend_schema(
    request=None,
    responses={200: ToggleWatchedInstrumentSerializer},
    summary="Toggle watched instrument",
    description="Toggle the watched status of an instrument for the current user.",
)
@api_view(["POST"])
@authentication_classes([ClerkAuthentication])
def toggle_watched_instrument(request: Request, instrument_id: str) -> Response:
    """
    Toggle the watched status of an instrument for the current user.
    """
    try:
        instrument = get_object_or_404(Instrument, id=instrument_id)
        investor = Investor.objects.get(clerk_id=request.user.id)

        if investor.watching_instruments.filter(id=instrument.id).exists():
            investor.watching_instruments.remove(instrument)
            is_watched = False
        else:
            investor.watching_instruments.add(instrument)
            is_watched = True

        serializer = ToggleWatchedInstrumentSerializer(
            {"is_watched": is_watched, "instrument_id": str(instrument.id)}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Investor.DoesNotExist:
        return Response(
            {"error": "Investor profile not found"},
            status=status.HTTP_404_NOT_FOUND,
        )
