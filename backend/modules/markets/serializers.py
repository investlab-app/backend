from polygon.rest.models.markets import MarketHoliday, MarketStatus
from rest_framework_dataclasses.serializers import DataclassSerializer


class MarketHolidaySerializer(DataclassSerializer):
    class Meta:
        dataclass = MarketHoliday


class MarketStatusSerializer(DataclassSerializer):
    class Meta:
        dataclass = MarketStatus
