from rest_framework import serializers

from modules.notifications.models import Notification, NotificationConfig


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for displaying notifications in the UI"""

    type_display = serializers.CharField(source="get_type_display", read_only=True)

    class Meta:
        model = Notification
        fields = [
            "id",
            "type",
            "type_display",
            "title",
            "message",
            "is_seen",
            "related_object_id",
            "related_object_type",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for marking notifications as seen"""

    class Meta:
        model = Notification
        fields = ["is_seen"]


class NotificationActionSerializer(serializers.Serializer):
    """Empty serializer for action endpoints that don't require a body"""

    pass


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


class NotificationConfigCreateSerializer(serializers.ModelSerializer):
    is_email = serializers.BooleanField()
    is_push = serializers.BooleanField()
    is_websocket = serializers.BooleanField()
    push_subscription = PushNotificationSerializer(required=False)

    class Meta:
        model = NotificationConfig
        fields = ["is_email", "is_push", "is_websocket", "push_subscription"]


class VapidPublicKeySerializer(serializers.Serializer):
    public_key = serializers.CharField()
