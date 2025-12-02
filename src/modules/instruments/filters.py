from django.db.models import Exists, OuterRef
from django_filters import rest_framework as drf_filters

from modules.instruments.models import Instrument
from modules.investors.models import Investor


class InstrumentFilterSet(drf_filters.FilterSet):
    watched = drf_filters.BooleanFilter(method="filter_watched")

    def filter_watched(self, queryset, name, value):
        m2m = Investor.watching_instruments.through.objects.filter(
            instrument_id=OuterRef("pk")
        )
        return queryset.annotate(is_watched=Exists(m2m)).filter(is_watched=value)

    class Meta:
        model = Instrument
        fields = []
