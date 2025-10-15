from django.db import transaction
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema_field
from rest_framework import serializers

from modules.instruments.models import Instrument
from modules.instruments.serializers import InstrumentNameSerializer
from modules.orders.models import MarketOrder, Order


class CreateMarketOrderSerializer(serializers.ModelSerializer):
    ticker = serializers.CharField(write_only=True)
    volume = serializers.DecimalField(
        min_value=0, max_digits=15, decimal_places=2, write_only=True
    )
    is_buy = serializers.BooleanField(write_only=True)

    class Meta:
        model = Order
        fields = ("id", "ticker", "volume", "is_buy", "investor")
        read_only_fields = ("id", "investor")

    def create(self, validated_data):
        instrument = get_object_or_404(Instrument, ticker=validated_data["ticker"])

        with transaction.atomic():
            detail = MarketOrder.objects.create(
                volume=validated_data["volume"],
                volume_processed=0,
                is_buy=validated_data["is_buy"],
            )

            order = Order.objects.create(
                ticker=instrument, investor=validated_data["investor"], detail=detail
            )

        return order

    def to_representation(self, instance):
        return OrderSerializer(instance).data


class MarketOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketOrder
        fields = ["volume", "volume_processed", "is_buy"]


class OrderSerializer(serializers.ModelSerializer):
    ticker = InstrumentNameSerializer()
    detail = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ["id", "ticker", "detail_type", "detail"]

    @extend_schema_field(
        PolymorphicProxySerializer(
            component_name="OrderDetail",
            serializers={
                "market": MarketOrderSerializer,
            },
            resource_type_field_name="detail_type",  # field to determine serializer
        )
    )
    def get_detail(self, obj):
        mapping = {MarketOrder: MarketOrderSerializer}
        return mapping[obj.detail_type.model_class()](obj.detail).data
