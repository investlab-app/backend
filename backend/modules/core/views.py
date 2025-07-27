from alpaca.data import (
    StockHistoricalDataClient,
)
from alpaca.data.requests import StockLatestBarRequest
from django.conf import settings
from drf_spectacular.utils import OpenApiResponse, extend_schema
from polygon import RESTClient
from rest_framework import permissions, serializers
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from modules.authentication.permissions import IsAdmin


class StatusResponseSerializer(serializers.Serializer):
    """Serializer for status endpoint response"""

    message = serializers.CharField(
        help_text="Status message indicating the application is running"
    )


class AuthTestResponseSerializer(serializers.Serializer):
    """Serializer for authentication test response"""

    message = serializers.CharField(help_text="Authentication success message")
    user_email = serializers.EmailField(help_text="Email of the authenticated user")
    user_id = serializers.IntegerField(help_text="ID of the authenticated user")


class SimpleResponseSerializer(serializers.Serializer):
    """Serializer for simple OK response"""

    OK = serializers.CharField(help_text="Simple confirmation response", default="OK")


class StatusView(GenericAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = StatusResponseSerializer

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=StatusResponseSerializer, description="Application status"
            )
        },
        summary="Get application status",
        description=(
            "Returns a simple status message indicating the application is running."
        ),
    )
    def get(self, _):
        return Response({"message": "App is running!"})


class AdminTestView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]
    serializer_class = AuthTestResponseSerializer

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=AuthTestResponseSerializer,
                description="Admin authentication test successful",
            )
        },
        summary="Test admin authentication",
        description="Test endpoint to verify admin authentication is working.",
    )
    def get(self, request):
        user = request.user
        return Response(
            {
                "message": "Authenticated successfully!",
                "user_email": user.email,
                "user_id": user.id,
            },
        )


class AuthTestView(GenericAPIView):
    serializer_class = AuthTestResponseSerializer

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=AuthTestResponseSerializer,
                description="Authentication test successful",
            )
        },
        summary="Test user authentication",
        description="Test endpoint to verify user authentication is working.",
    )
    def get(self, request):
        user = request.user
        return Response(
            {
                "message": "Authenticated successfully!",
                "user_email": user.email,
                "user_id": user.id,
            },
        )


class UnauthTestView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SimpleResponseSerializer

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=SimpleResponseSerializer,
                description="Unauthenticated test successful",
            )
        },
        summary="Test unauthenticated endpoint",
        description="Test endpoint that doesn't require authentication.",
    )
    def get(self, _):
        return Response({"OK": "OK"})


class PolygonTestView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SimpleResponseSerializer

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=SimpleResponseSerializer,
                description="Last trade result from Polygon",
            )
        },
        summary="Fetch last trade from Polygon.io",
        description="test polygon.",
    )
    def get(self, _):
        client = RESTClient(api_key=settings.POLYGON_SECRET_KEY)
        resp = client.get_previous_close_agg(
            "AAPL",
            adjusted=True,
        )
        print(resp)
        return Response(str(resp))


class AlpacaTestView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = SimpleResponseSerializer

    @extend_schema(
        responses={
            200: OpenApiResponse(
                response=SimpleResponseSerializer,
                description="Last trade result from Alpaca",
            )
        },
        summary="Fetch last trade from Alpaca",
        description="test alpaca.",
    )
    def get(self, _):
        client = StockHistoricalDataClient(
            settings.ALPACA_PUBLIC_KEY, settings.ALPACA_SECRET_KEY
        )
        request = StockLatestBarRequest(symbol_or_symbols="AAPL")
        response = client.get_stock_latest_bar(request_params=request)
        print(response)
        return Response(str(response))
