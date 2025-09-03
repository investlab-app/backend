import logging
import random
from datetime import date, timedelta

from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from modules.authentication.clerk_auth import ClerkAuthentication
from modules.investors.models import Investor
from modules.investors.serializers import (
    AccountValueOverTimeSerializer,
    AssetAllocationSerializer,
    CurrentAccountValueSerializer,
    InvestorExpSerializer,
    InvestorListQueryParams,
    InvestorSerializer,
    InvestorStatsSerializer,
    InvestorUpdateSerializer,
    OwnedSharesSerializer,
)

logger = logging.getLogger(__name__)


class InvestorListView(generics.ListAPIView):
    """
    List all investors.
    """

    queryset = Investor.objects.prefetch_related("watching_instruments")
    serializer_class = InvestorSerializer
    authentication_classes = [ClerkAuthentication]
    permission_classes = [IsAuthenticated]

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
    authentication_classes = [ClerkAuthentication]
    permission_classes = [IsAuthenticated]
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
    authentication_classes = [ClerkAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            print(self.request.user.id)
            return Investor.objects.prefetch_related("watching_instruments").get(
                clerk_id=self.request.user.id
            )
        except Investor.DoesNotExist:
            return Investor.objects.create(clerk_id=self.request.user.id)

    @extend_schema(
        responses={200: InvestorSerializer},
        summary="Get current investor",
        description="Get the investor profile for the currently authenticated user.",
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)


class InvestorExpView(generics.RetrieveAPIView):
    """
    Get investor exp and level for the current authenticated user.
    """
    serializer_class = InvestorExpSerializer
    authentication_classes = [ClerkAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return Investor.objects.get(clerk_id=self.request.user.id)
        except Investor.DoesNotExist:
            return Investor.objects.create(clerk_id=self.request.user.id)

    @extend_schema(
        responses={200: InvestorExpSerializer},
        summary="Get investor's exp and level",
        description=(
            "Get investor exp and level for the currently authenticated user."
        ),
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
        try:
            return Investor.objects.get(clerk_id=self.request.user.id)
        except Investor.DoesNotExist:
            return Investor.objects.create(clerk_id=self.request.user.id)

    def retrieve(self, request, *args, **kwargs):
        # Generate random stats data
        # Using user ID as seed for consistent data per user
        random.seed(hash(self.request.user.id))

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
        try:
            return Investor.objects.get(clerk_id=self.request.user.id)
        except Investor.DoesNotExist:
            return Investor.objects.create(clerk_id=self.request.user.id)

    def retrieve(self, request, *args, **kwargs):
        # Generate random account value data over time
        # Using user ID as seed for consistent data per user
        random.seed(hash(self.request.user.id))

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


class CurrentAccountValueView(generics.RetrieveAPIView):
    """
    Get the current account value for the authenticated user.
    """

    serializer_class = CurrentAccountValueSerializer
    authentication_classes = [ClerkAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return Investor.objects.get(clerk_id=self.request.user.id)
        except Investor.DoesNotExist:
            return Investor.objects.create(clerk_id=self.request.user.id)

    def retrieve(self, request, *args, **kwargs):
        # Generate random account value for today, keeping it consistent with
        # the AccountValueOverTimeView endpoint.
        # Using user ID as seed for consistent data per user
        random.seed(hash(self.request.user.id))

        # This calculation mimics the first (most recent) value generated
        # in the AccountValueOverTimeView.
        base_value = random.uniform(100, 200)
        variation = random.uniform(-0.1, 0.1)  # First variation
        value = base_value * (1 + variation)

        current_value = {"value": round(value, 2)}

        serializer = self.get_serializer(current_value)
        return Response(serializer.data)

    @extend_schema(
        responses={200: CurrentAccountValueSerializer},
        summary="Get current account value",
        description="Get the current account value for the authenticated user.",
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)


class AssetAllocationView(generics.RetrieveAPIView):
    """
    Get asset allocation data for the current authenticated user.
    """

    serializer_class = AssetAllocationSerializer
    authentication_classes = [ClerkAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return Investor.objects.get(clerk_id=self.request.user.id)
        except Investor.DoesNotExist:
            return Investor.objects.create(clerk_id=self.request.user.id)

    def retrieve(self, request, *args, **kwargs):
        # Using user ID as seed for consistent data per user
        random.seed(hash(self.request.user.id))

        # Generate realistic-looking stats
        invested = round(random.uniform(20000, 75000), 2)
        total_return_this_year = round(
            random.uniform(-invested * 0.1, invested * 0.15), 2
        )
        total_value = invested + total_return_this_year

        # Generate allocations
        allocations = []
        remaining_percentage = 1.0

        # Stocks
        stocks_percentage = round(random.uniform(0.6, 0.8), 4)
        remaining_percentage -= stocks_percentage
        allocations.append(
            {
                "asset_class_display_name": "Stocks",
                "value": round(total_value * stocks_percentage, 2),
                "percentage": round(stocks_percentage * 100, 2),
            }
        )

        # Bonds
        bonds_percentage = round(random.uniform(0.1, remaining_percentage * 0.9), 4)
        remaining_percentage -= bonds_percentage
        allocations.append(
            {
                "asset_class_display_name": "Bonds",
                "value": round(total_value * bonds_percentage, 2),
                "percentage": round(bonds_percentage * 100, 2),
            }
        )

        # Unallocated
        unallocated_percentage = remaining_percentage
        allocations.append(
            {
                "asset_class_display_name": "Unallocated",
                "value": round(total_value * unallocated_percentage, 2),
                "percentage": round(unallocated_percentage * 100, 2),
            }
        )

        # Recalculate total value from parts to avoid rounding errors
        calculated_total_value = sum(item["value"] for item in allocations)

        response_data = {
            "total_value": calculated_total_value,
            "total_return_this_year": total_return_this_year,
            "allocations": allocations,
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

    serializer_class = OwnedSharesSerializer
    authentication_classes = [ClerkAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            return Investor.objects.get(clerk_id=self.request.user.id)
        except Investor.DoesNotExist:
            return Investor.objects.create(clerk_id=self.request.user.id)

    def retrieve(self, request, *args, **kwargs):
        random.seed(hash(self.request.user.id))

        owned_shares_data = [
            {
                "name": "Apple Inc.",
                "symbol": "AAPL",
                "volume": round(random.uniform(1, 10), 5),
                "value": round(random.uniform(150, 250), 2),
                "profit": round(random.uniform(-5, 5), 2),
            },
            {
                "name": "Tesla, Inc.",
                "symbol": "TSLA",
                "volume": round(random.uniform(1, 10), 5),
                "value": round(random.uniform(200, 300), 2),
                "profit": round(random.uniform(-10, 10), 2),
            },
            {
                "name": "Amazon.com, Inc.",
                "symbol": "AMZN",
                "volume": round(random.uniform(0.1, 2), 5),
                "value": round(random.uniform(100, 200), 2),
                "profit": round(random.uniform(-5, 5), 2),
            },
            {
                "name": "Microsoft Corp.",
                "symbol": "MSFT",
                "volume": round(random.uniform(1, 5), 5),
                "value": round(random.uniform(300, 450), 2),
                "profit": round(random.uniform(-2, 2), 2),
            },
            {
                "name": "NVIDIA Corp.",
                "symbol": "NVDA",
                "volume": round(random.uniform(0.5, 3), 5),
                "value": round(random.uniform(800, 1000), 2),
                "profit": round(random.uniform(-15, 15), 2),
            },
            {
                "name": "Alphabet Inc.",
                "symbol": "GOOGL",
                "volume": round(random.uniform(1, 2), 5),
                "value": round(random.uniform(130, 180), 2),
                "profit": round(random.uniform(5, 20), 2),
            },
        ]

        # for each share, recalculate profit_percentage from value and profit
        for share in owned_shares_data:
            purchase_price = share["value"] - share["profit"]
            if purchase_price != 0:
                share["profit_percentage"] = round(
                    (share["profit"] / purchase_price) * 100, 2
                )
            else:
                share["profit_percentage"] = 0

        response_data = {"owned_shares": owned_shares_data}

        serializer = self.get_serializer(response_data)
        return Response(serializer.data)

    @extend_schema(
        responses={200: OwnedSharesSerializer},
        summary="Get owned shares",
        description="Get owned shares data for the currently authenticated user.",
    )
    def get(self, request: Request, *args, **kwargs) -> Response:
        return super().get(request, *args, **kwargs)
