import logging

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
    InvestorCreateSerializer,
    InvestorListQueryParams,
    InvestorSerializer,
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
