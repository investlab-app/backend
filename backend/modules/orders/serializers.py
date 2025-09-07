from rest_framework import serializers
from django.shortcuts import get_object_or_404

from modules.orders.models import Order, MarketOrder
from modules.instruments.models import Instrument
from modules.instruments.serializers import InstrumentNameSerializer

class CreateMarketOrderSerializer(serializers.ModelSerializer):
    ticker = serializers.CharField(write_only=True)
    volume = serializers.IntegerField(min_value=1, write_only=True)
    is_buy = serializers.BooleanField(write_only=True)

    class Meta:
        model = Order
        fields = ('id', 'ticker', 'volume', 'is_buy', 'investor')
        read_only_fields = ('id', 'investor')

    def create(self, validated_data):
        instrument = get_object_or_404(Instrument, ticker=validated_data['ticker'])
        
        detail = MarketOrder.objects.create(
            volume=validated_data['volume'],
            volume_processed=validated_data['volume'],
            is_buy=validated_data['is_buy']
        )

        order = Order.objects.create(
            ticker=instrument,
            investor=validated_data['investor'],
            detail=detail
        )
        return order

    def to_representation(self, instance):
        return OrderSerializer(instance).data


class OrderSerializer(serializers.ModelSerializer):
    ticker = InstrumentNameSerializer()
    detail = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = ['id', 'ticker', 'detail']

    def get_detail(self, obj):
        mapping = {
            MarketOrder: MarketOrderSerializer
        }
        return mapping[obj.detail_type.model_class()](obj.detail).data

class MarketOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketOrder
        fields = ['volume', 'volume_processed', 'is_buy']
