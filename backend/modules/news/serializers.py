from rest_framework import serializers
from rest_framework_dataclasses.serializers import DataclassSerializer
from polygon.rest.models.tickers import TickerNews


class NewsListQueryParams(serializers.Serializer):
    ticker = serializers.CharField(required=False, allow_blank=True)
    published_utc = serializers.DateTimeField(required=False)
    published_utc_lt = serializers.DateTimeField(required=False)
    published_utc_lte = serializers.DateTimeField(required=False)
    published_utc_gt = serializers.DateTimeField(required=False)
    published_utc_gte = serializers.DateTimeField(required=False)
    sort = serializers.CharField(required=False, default="published_utc")
    order = serializers.ChoiceField(choices=["asc", "desc"], required=False, default="desc")


class TickerNewsSerializer(DataclassSerializer):
    class Meta:
        dataclass = TickerNews
