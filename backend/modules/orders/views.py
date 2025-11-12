from django.contrib.contenttypes.models import ContentType
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response

from modules.investors.models import Investor
from modules.orders.models import LimitOrder, MarketOrder, Order
from modules.orders.serializers import (
    CreateLimitOrderSerializer,
    CreateMarketOrderSerializer,
    FilterOrdersSerializer,
    OrderSerializer,
)
from modules.orders.services.order_services import OrderService


class MarketOrderView(generics.GenericAPIView):
    pagination_class = None

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateMarketOrderSerializer
        return OrderSerializer

    @extend_schema(
        request=CreateMarketOrderSerializer,
        responses={201: OrderSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        parameters=[FilterOrdersSerializer],
        responses={200: OrderSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data})

    def perform_create(self, serializer):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        serializer.save(investor=investor)

    def get_queryset(self):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        market_order_ct = ContentType.objects.get_for_model(MarketOrder)
        queryset = Order.objects.filter(investor=investor, detail_type=market_order_ct)

        ticker = self.request.query_params.get("ticker", None)
        if ticker:
            queryset = queryset.filter(ticker__ticker=ticker)

        return queryset


class LimitOrderView(generics.GenericAPIView):
    pagination_class = None

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateLimitOrderSerializer
        return OrderSerializer

    @extend_schema(
        request=CreateLimitOrderSerializer,
        responses={201: OrderSerializer},
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        parameters=[FilterOrdersSerializer],
        responses={200: OrderSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"results": serializer.data})

    def perform_create(self, serializer):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        serializer.save(investor=investor)

    def get_queryset(self):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        limit_order_ct = ContentType.objects.get_for_model(LimitOrder)
        queryset = Order.objects.filter(investor=investor, detail_type=limit_order_ct)

        ticker = self.request.query_params.get("ticker", None)
        if ticker:
            queryset = queryset.filter(ticker__ticker=ticker)

        return queryset


class ListOrderView(generics.ListAPIView):
    serializer_class = OrderSerializer
    pagination_class = None

    @extend_schema(
        parameters=[FilterOrdersSerializer],
        responses={200: OrderSerializer(many=True)},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        queryset = Order.objects.filter(investor=investor)

        ticker = self.request.query_params.get("ticker", None)
        if ticker:
            queryset = queryset.filter(ticker__ticker=ticker)

        return queryset


class DestroyOrderView(generics.DestroyAPIView):
    serializer_class = OrderSerializer
    lookup_field = "id"

    def get_queryset(self):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        return Order.objects.filter(investor=investor)

    def perform_destroy(self, instance):
        OrderService().delete(instance)
