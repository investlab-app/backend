from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics

from modules.investors.models import Investor
from modules.orders.models import LimitOrder, MarketOrder, Order
from modules.orders.serializers import (
    CreateLimitOrderSerializer,
    CreateMarketOrderSerializer,
    OrderSerializer,
)
from modules.orders.services.order_services import LimitOrderService, MarketOrderService


class CreateMarketOrderView(generics.CreateAPIView):
    serializer_class = CreateMarketOrderSerializer

    @extend_schema(responses={201: OrderSerializer})
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        serializer.save(investor=investor)


class CreateLimitOrderView(generics.CreateAPIView):
    serializer_class = CreateLimitOrderSerializer

    @extend_schema(responses={201: OrderSerializer})
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        serializer.save(investor=investor)


class ListOrderView(generics.ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        return Order.objects.filter(investor=investor)


class DestroyOrderView(generics.DestroyAPIView):
    serializer_class = OrderSerializer
    lookup_field = "id"

    def get_queryset(self):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        return Order.objects.filter(investor=investor)

    def perform_destroy(self, instance):
        # Choose deletion service based on underlying detail type
        if isinstance(instance.detail, MarketOrder):
            MarketOrderService().delete(instance)
        elif isinstance(instance.detail, LimitOrder):
            LimitOrderService().delete(instance)
        else:
            raise ValueError("Object not supported")
