from rest_framework import serializers

from modules.instruments.models import Instrument
from modules.investors.models import Investor
from modules.notifications.models import PriceAlert, PushSubscription


class NotificationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationConfig
        fields = [
            "id",
            "is_email",
            "is_push",
            "is_websocket",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class PushNotificationSerializer(serializers.Serializer):
    endpoint = serializers.URLField(write_only=True)
    p256dh = serializers.CharField(max_length=255, write_only=True)
    auth = serializers.CharField(max_length=255, write_only=True)


class NotificationCreateSerializer(serializers.ModelSerializer):
    is_email = serializers.BooleanField()
    is_push = serializers.BooleanField()
    is_websocket = serializers.BooleanField()
    push_subscription = PushNotificationSerializer(required=False)

    class Meta:
        model = NotificationConfig
        fields = ["is_email", "is_push", "is_websocket", "push_subscription"]

