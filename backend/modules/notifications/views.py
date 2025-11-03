import logging

from drf_spectacular.utils import extend_schema
from rest_framework import generics, viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from config.settings import VAPID_PUBLIC_KEY
from modules.notifications.models import Notification
from modules.notifications.serializers import (
    VapidPublicKeySerializer,
    NotificationSerializer,
    NotificationUpdateSerializer,
    NotificationActionSerializer,
)

logger = logging.getLogger(__name__)


class VapidPublicKeyView(generics.RetrieveAPIView):
    serializer_class = VapidPublicKeySerializer

    def retrieve(self, request, *args, **kwargs):
        return Response({"public_key": VAPID_PUBLIC_KEY})


class NotificationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for retrieving and managing user notifications.

    Actions:
    - list: Get all notifications for current user
    - retrieve: Get a specific notification
    - partial_update: Mark a notification as seen/unseen
    - mark_all_as_seen (POST /api/notifications/mark_all_as_seen/): Mark all as seen
    - unseen_count (GET /api/notifications/unseen_count/): Get count of unseen
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "patch", "post", "head", "options"]

    def get_queryset(self):
        """Filter notifications for the current user"""
        return Notification.objects.filter(
            investor__clerk_id=self.request.user.id
        ).order_by("-created_at")

    def get_serializer_class(self):
        """Use appropriate serializer for each action"""
        if self.action in ["partial_update"]:
            return NotificationUpdateSerializer
        if self.action in ["mark_all_as_seen"]:
            return NotificationActionSerializer
        return NotificationSerializer

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated],
    )
    def mark_all_as_seen(self, request):
        """Mark all notifications as seen for the current user"""
        queryset = self.get_queryset()
        count = queryset.filter(is_seen=False).update(is_seen=True)
        return Response(
            {
                "detail": "All notifications marked as seen",
                "updated_count": count,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(responses={200: int})
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[IsAuthenticated],
    )
    def unseen_count(self, request):
        """Get count of unseen notifications for the current user"""
        queryset = self.get_queryset()
        unseen_count = queryset.filter(is_seen=False).count()
        return Response(unseen_count, status=status.HTTP_200_OK)
