from django.shortcuts import get_object_or_404
from rest_framework import generics

from modules.investors.models import Investor
from modules.orders.models import Order
from modules.orders.serializers import CreateMarketOrderSerializer, OrderSerializer
from modules.orders.services.order_services import MarketOrderService


class CreateMarketOrderView(generics.CreateAPIView):
    serializer_class = CreateMarketOrderSerializer

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
        service = MarketOrderService()
        service.delete(instance)
