from django.shortcuts import get_object_or_404
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema_field
from rest_framework import serializers

from modules.instruments.models import Instrument
from modules.orders.models import LimitOrder, MarketOrder, Order
from modules.orders.services.order_services import OrderFailureReason, OrderService


class FilterOrdersSerializer(serializers.Serializer):
    ticker = serializers.CharField(
        max_length=20,
        required=False,
        help_text=(
            "Filter orders by instrument ticker (e.g., 'AAPL'). "
            "If not provided, returns orders for all instruments."
        ),
    )


class CreateMarketOrderSerializer(serializers.ModelSerializer):
    ticker = serializers.CharField(write_only=True)
    volume = serializers.DecimalField(
        min_value=0, max_digits=15, decimal_places=5, write_only=True
    )
    is_buy = serializers.BooleanField(write_only=True)

    class Meta:
        model = Order
        fields = ("id", "ticker", "volume", "is_buy", "investor")
        read_only_fields = ("id", "investor")

    def create(self, validated_data):
        instrument = get_object_or_404(Instrument, ticker=validated_data["ticker"])
        service = OrderService()
        order, err = service.create_market(
            instrument=instrument,
            investor=validated_data["investor"],
            volume=validated_data["volume"],
            is_buy=validated_data["is_buy"],
        )
        if not order:
            if err == "funsd":
                raise serializers.ValidationError(
                    "Cannot create market order due to blocked funds"
                )
            if err == "assets":
                raise serializers.ValidationError(
                    "Cannot create market order due to insufficient assets"
                )

        return order

    def to_representation(self, instance):
        return OrderSerializer(instance).data


class CreateLimitOrderSerializer(serializers.ModelSerializer):
    ticker = serializers.CharField(write_only=True)
    volume = serializers.DecimalField(
        min_value=0, max_digits=15, decimal_places=5, write_only=True
    )
    is_buy = serializers.BooleanField(write_only=True)
    limit_price = serializers.DecimalField(
        min_value=0, max_digits=30, decimal_places=8, write_only=True
    )

    class Meta:
        model = Order
        fields = ("id", "ticker", "volume", "is_buy", "limit_price", "investor")
        read_only_fields = ("id", "investor")

    def create(self, validated_data):
        instrument = get_object_or_404(Instrument, ticker=validated_data["ticker"])
        service = OrderService()
        order, err = service.create_limit(
            instrument=instrument,
            investor=validated_data["investor"],
            volume=validated_data["volume"],
            is_buy=validated_data["is_buy"],
            limit_price=validated_data["limit_price"],
        )
        if not order:
            if err ==  OrderFailureReason.FUNDS:
                raise serializers.ValidationError(
                    "Cannot create limit order due to blocked funds"
                )
            if err ==  OrderFailureReason.ASSETS:
                raise serializers.ValidationError(
                    "Cannot create limit order due to insufficient assets"
                )

        return order

    def to_representation(self, instance):
        return OrderSerializer(instance).data


class MarketOrderDetailsSerializer(serializers.ModelSerializer):
    detail_type = serializers.SerializerMethodField()

    class Meta:
        model = MarketOrder
        fields = ["detail_type", "volume", "volume_processed", "is_buy"]

    def get_detail_type(self, obj) -> str:
        return "market"


class LimitOrderDetailsSerializer(serializers.ModelSerializer):
    detail_type = serializers.SerializerMethodField()

    class Meta:
        model = LimitOrder
        fields = ["detail_type", "volume", "volume_processed", "is_buy", "limit_price"]

    def get_detail_type(self, obj) -> str:
        return "limit"


class OrderSerializer(serializers.ModelSerializer):
    ticker = serializers.CharField(source="ticker.ticker", read_only=True)
    detail = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ["id", "ticker", "detail_type", "detail"]

    @extend_schema_field(
        PolymorphicProxySerializer(
            component_name="OrderDetail",
            serializers={
                "market": MarketOrderDetailsSerializer,
                "limit": LimitOrderDetailsSerializer,
            },
            resource_type_field_name="detail_type",  # field to determine serializer
        )
    )
    def get_detail(self, obj):
        mapping = {
            MarketOrder: MarketOrderDetailsSerializer,
            LimitOrder: LimitOrderDetailsSerializer,
        }
        return mapping[obj.detail_type.model_class()](obj.detail).data


class LimitOrderSerializer(serializers.ModelSerializer):
    ticker = serializers.CharField(source="ticker.ticker", read_only=True)
    detail = LimitOrderDetailsSerializer()

    class Meta:
        model = Order
        fields = ["id", "ticker", "detail_type", "detail"]


class MarketOrderSerializer(serializers.ModelSerializer):
    ticker = serializers.CharField(source="ticker.ticker", read_only=True)
    detail = MarketOrderDetailsSerializer()

    class Meta:
        model = Order
        fields = ["id", "ticker", "detail_type", "detail"]
