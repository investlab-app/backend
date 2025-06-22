import logging
import random
from datetime import date, timedelta

from django.db.models import Q
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from modules.authentication.clerk_auth import ClerkAuthentication
from modules.investors.models import Investor
from modules.investors.serializers import (
    AccountValueOverTimeSerializer,
    InvestorCreateSerializer,
    InvestorListQueryParams,
    InvestorSerializer,
    InvestorStatsSerializer,
    InvestorUpdateSerializer,
)

logger = logging.getLogger(__name__)


class InvestorPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class InvestorListCreateView(generics.ListCreateAPIView):
    """
    List all investors or create a new investor.
    """

    queryset = Investor.objects.select_related("user").prefetch_related(
        "watching_instruments"
    )
    serializer_class = InvestorSerializer
    authentication_classes = [ClerkAuthentication]
    permission_classes = [IsAuthenticated]
    pagination_class = InvestorPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return InvestorCreateSerializer
        return InvestorSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get("search", "")

        if search:
            queryset = queryset.filter(
                Q(user__email__icontains=search)
                | Q(user__first_name__icontains=search)
                | Q(user__last_name__icontains=search)
            )

        return queryset.order_by("-id")

    @extend_schema(
        parameters=[InvestorListQueryParams],
        responses={200: InvestorSerializer(many=True)},
        summary="List investors",
        description="Get a paginated list of investors with optional search filtering.",
    )
    def get(self, request: Request) -> Response:
        return super().get(request)

    @extend_schema(
        request=InvestorCreateSerializer,
        responses={201: InvestorSerializer},
        summary="Create investor",
        description="Create a new investor associated with a user.",
    )
    def post(self, request: Request) -> Response:
        return super().post(request)


class InvestorDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update, or delete an investor.
    """

    queryset = Investor.objects.select_related("user").prefetch_related(
        "watching_instruments"
    )
    serializer_class = InvestorSerializer
    authentication_classes = [ClerkAuthentication]
    permission_classes = [IsAuthenticated]

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

    @extend_schema(
        responses={204: None},
        summary="Delete investor",
        description="Delete an investor.",
    )
    def delete(self, request: Request, *args, **kwargs) -> Response:
        return super().delete(request, *args, **kwargs)


class CurrentInvestorView(generics.RetrieveAPIView):
    """
    Get the current authenticated user's investor profile.
    """

    serializer_class = InvestorSerializer
    authentication_classes = [ClerkAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return (
                Investor.objects.select_related("user")
                .prefetch_related("watching_instruments")
                .get(user=self.request.user)
            )
        except Investor.DoesNotExist:
            # Create investor if it doesn't exist
            return Investor.objects.create(user=self.request.user)

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
    authentication_classes = [ClerkAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Ensure investor exists for the current user
        try:
            return Investor.objects.get(user=self.request.user)
        except Investor.DoesNotExist:
            return Investor.objects.create(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        # Generate random stats data
        # Using user ID as seed for consistent data per user
        random.seed(self.request.user.id)

        # Generate realistic-looking stats
        invested = round(random.uniform(1000, 50000), 2)
        total_return = round(random.uniform(-invested * 0.3, invested * 0.5), 2)
        todays_return = round(random.uniform(-invested * 0.05, invested * 0.05), 2)
        total_value = invested + total_return

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


class AccountValueOverTimeView(generics.RetrieveAPIView):
    """
    Get account value over time data for the current authenticated user.
    """

    serializer_class = AccountValueOverTimeSerializer
    authentication_classes = [ClerkAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Ensure investor exists for the current user
        try:
            return Investor.objects.get(user=self.request.user)
        except Investor.DoesNotExist:
            return Investor.objects.create(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        # Generate random account value data over time
        # Using user ID as seed for consistent data per user
        random.seed(self.request.user.id)

        # Generate 120 data points (approximately 4 months of weekly data)
        data_points = []
        today = date.today()
        base_value = random.uniform(100, 200)

        for i in range(120):
            # Go back in time by weeks
            data_date = today - timedelta(weeks=i)

            # Add some realistic variation to the base value
            variation = random.uniform(-0.1, 0.1)  # ±10% variation
            value = base_value * (1 + variation)

            data_points.append(
                {"date": data_date.isoformat(), "value": round(value, 2)}
            )

        # Reverse to get chronological order (oldest first)
        data_points.reverse()

        response_data = {"data": data_points}

        serializer = self.get_serializer(response_data)
        return Response(serializer.data)

    @extend_schema(
        responses={200: AccountValueOverTimeSerializer},
        summary="Get account value over time",
        description=(
            "Get account value over time data for the currently authenticated user."
        ),
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)
