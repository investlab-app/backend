from rest_framework import serializers

from modules.instruments.models import Instrument
from modules.investors.models import Investor
from modules.notifications.models import PriceAlert, PushSubscription


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        abstract = True
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
        abstract = True
        fields = ["is_email", "is_push", "is_websocket", "push_subscription"]


class PriceAlertSerializer(NotificationSerializer):
    instrument_name = serializers.CharField(source="instrument.name", read_only=True)
    instrument_ticker = serializers.CharField(
        source="instrument.ticker", read_only=True
    )

    class Meta(NotificationSerializer.Meta):
        model = PriceAlert
        fields = NotificationSerializer.Meta.fields + [
            "instrument_name",
            "instrument_ticker",
            "threshold_type",
            "threshold_value",
        ]


class PriceAlertCreateSerializer(NotificationCreateSerializer):
    instrument_ticker = serializers.CharField(write_only=True)

    class Meta(NotificationCreateSerializer.Meta):
        model = PriceAlert
        fields = NotificationCreateSerializer.Meta.fields + [
            "instrument_ticker",
            "threshold_type",
            "threshold_value",
        ]

    def validate_instrument_ticker(self, value):
        if not Instrument.objects.filter(ticker=value).exists():
            raise serializers.ValidationError(
                f"Instrument with ticker '{value}' does not exist."
            )
        return value

    def create(self, validated_data):
        push_subscription = validated_data.pop("push_subscription", None)
        instrument_ticker = validated_data.pop("instrument_ticker")

        # Get the instrument
        try:
            instrument = Instrument.objects.get(ticker=instrument_ticker)
        except Instrument.DoesNotExist as err:
            raise serializers.ValidationError(
                f"Instrument with ticker '{instrument_ticker}' does not exist."
            ) from err

        # Get the investor
        request = self.context.get("request")
        if not request or not request.user:
            raise serializers.ValidationError("User must be authenticated.")

        try:
            investor = Investor.objects.get(clerk_id=request.user.id)
        except Investor.DoesNotExist as err:
            raise serializers.ValidationError("Investor profile not found.") from err

        # Create or update the PriceAlert
        price_alert, _ = PriceAlert.objects.update_or_create(
            investor=investor,
            instrument=instrument,
            threshold_type=validated_data["threshold_type"],
            threshold_value=validated_data["threshold_value"],
            defaults={
                "is_email": validated_data["is_email"],
                "is_push": validated_data["is_push"],
                "is_websocket": validated_data.get("is_websocket", True),
                "is_active": validated_data.get("is_active", True),
            },
        )

        # Create PushSubscription
        if push_subscription:
            PushSubscription.objects.update_or_create(
                investor=investor,
                endpoint=push_subscription["endpoint"],
                p256dh=push_subscription["p256dh"],
                auth=push_subscription["auth"],
            )

        return price_alert
