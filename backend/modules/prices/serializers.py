from rest_framework import serializers
from rest_framework_dataclasses.serializers import DataclassSerializer

from config.settings import ACCEPTABLE_DATETIME_FORMATS
from modules.instruments.models import Instrument
from modules.notifications.models import NotificationConfig, PushSubscription
from modules.notifications.serializers import (
    NotificationConfigCreateSerializer,
    NotificationConfigSerializer,
)
from modules.prices.constants import POLYGON_INTERVALS
from modules.prices.models import PriceAlert
from modules.prices.schemas import PriceBar, PriceDailySummary


class PriceBarsQueryParams(serializers.Serializer):
    ticker = serializers.CharField(required=True, max_length=6)
    start_date = serializers.DateTimeField(
        required=True, input_formats=ACCEPTABLE_DATETIME_FORMATS
    )
    end_date = serializers.DateTimeField(
        input_formats=ACCEPTABLE_DATETIME_FORMATS, default="2025-09-23T00:00:00Z"
    )
    interval = serializers.ChoiceField(choices=POLYGON_INTERVALS)
    interval_multiplier = serializers.IntegerField(default=1, min_value=1)

    def validate(self, attrs):
        if attrs["start_date"] >= attrs["end_date"]:
            raise serializers.ValidationError("Start date must be before end date")
        return super().validate(attrs)


class PricesListQueryParams(serializers.Serializer):
    tickers = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        allow_empty=False,
        max_length=50,
        help_text="List of ticker symbols to fetch prices for (max 50).",
    )


class PriceBarSerializer(DataclassSerializer):
    class Meta:
        dataclass = PriceBar


class PriceDailySummarySerializer(DataclassSerializer):
    class Meta:
        dataclass = PriceDailySummary


class PriceAlertSerializer(serializers.ModelSerializer):
    notification_config = NotificationConfigSerializer()
    instrument_name = serializers.CharField(source="instrument.name", read_only=True)
    instrument_ticker = serializers.CharField(
        source="instrument.ticker", read_only=True
    )

    class Meta:
        model = PriceAlert
        fields = [
            "id",
            "instrument_name",
            "instrument_ticker",
            "threshold_type",
            "threshold_value",
            "notification_config",
        ]


class PriceAlertCreateSerializer(serializers.ModelSerializer):
    instrument_ticker = serializers.CharField(write_only=True)
    notification_config = NotificationConfigCreateSerializer()

    class Meta:
        model = PriceAlert
        fields = [
            "id",
            "instrument_ticker",
            "threshold_type",
            "threshold_value",
            "notification_config",
        ]

    def validate_instrument_ticker(self, value):
        try:
            instrument = Instrument.objects.get(ticker=value.upper())
        except Instrument.DoesNotExist as e:
            raise serializers.ValidationError(
                "Instrument with this ticker does not exist."
            ) from e
        return instrument

    def create(self, validated_data):
        investor = validated_data.pop("investor")
        instrument = validated_data.pop("instrument_ticker")
        notification_data = validated_data.pop("notification_config")

        push_subscription = notification_data.pop("push_subscription", None)
        if push_subscription:
            PushSubscription.objects.get_or_create(
                **push_subscription, defaults={"investor": investor}
            )

        notification_config = NotificationConfig.objects.create(**notification_data)

        price_alert = PriceAlert.objects.create(
            investor=investor,
            instrument=instrument,
            notification_config=notification_config,
            **validated_data,
        )
        return price_alert
