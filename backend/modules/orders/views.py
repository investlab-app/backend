from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics

from modules.investors.models import Investor
from modules.orders.models import Order
from modules.orders.serializers import CreateMarketOrderSerializer, OrderSerializer


class CreateMarketOrderView(generics.CreateAPIView):
    serializer_class = CreateMarketOrderSerializer

    @extend_schema(responses={201: OrderSerializer})
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def perform_create(self, serializer):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)

        # Validate balance and allocate money for buy orders
        validated_data = serializer.validated_data
        if validated_data.get("is_buy"):
            order_cost = validated_data["volume"]  # Simplified: volume as cost proxy

            if investor.balance < order_cost:
                raise ValueError("Insufficient balance to create this order")

            # Allocate money: deduct from balance, add to buffer
            with transaction.atomic():
                investor.balance -= order_cost
                investor.buffer_money += order_cost
                investor.save()

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
