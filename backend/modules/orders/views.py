from django.shortcuts import get_object_or_404
from rest_framework import generics

from modules.investors.models import Investor
from modules.orders.serializers import *
from modules.orders.models import Order

class CreateMarketOrderView(generics.CreateAPIView):
    serializer_class = CreateMarketOrderSerializer

    def perform_create(self, serializer):
        investor = get_object_or_404(Investor, user=self.request.user)
        serializer.save(investor=investor)

class ListOrderView(generics.ListAPIView):
    serializer_class = OrderSerializer

    def get_queryset(self):
        investor = get_object_or_404(Investor, user=self.request.user)
        return Order.objects.filter(investor = investor)


class DestroyOrderView(generics.DestroyAPIView):
    serializer_class = OrderSerializer
    lookup_field = 'id'

    def get_queryset(self):
        investor = get_object_or_404(Investor, user=self.request.user)
        return Order.objects.filter(investor = investor)
    