import logging

from rest_framework import generics
from rest_framework.response import Response

from config.settings import VAPID_PUBLIC_KEY

from .models import PriceAlert
from .serializers import (
    PriceAlertCreateSerializer,
    PriceAlertSerializer,
)

logger = logging.getLogger(__name__)


class PriceAlertListCreateView(generics.ListCreateAPIView):
    serializer_class = PriceAlertSerializer

    def get_queryset(self):
        clerk_id = self.request.user.id
        return PriceAlert.objects.filter(
            investor__clerk_id=clerk_id, is_active=True
        ).select_related("instrument")

    def get_serializer_class(self):
        if self.request.method == "POST":
            return PriceAlertCreateSerializer
        return PriceAlertSerializer


class PriceAlertDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PriceAlertSerializer

    def get_queryset(self):
        clerk_id = self.request.user.id
        return PriceAlert.objects.filter(investor__clerk_id=clerk_id)


class VapidPublicKeyView(generics.RetrieveAPIView):
    def retrieve(self, request, *args, **kwargs):
        return Response({"public_key": VAPID_PUBLIC_KEY})
