from rest_framework import filters, generics

from modules.core.pagination import DynamicPageSizePagination
from modules.instruments_v3.models import Instrument
from modules.instruments_v3.serializers import InstrumentListSerializer


class InstrumentsListView(generics.ListAPIView):
    queryset = Instrument.objects.all()
    serializer_class = InstrumentListSerializer
    pagination_class = DynamicPageSizePagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["ticker"]
    ordering_fields = ["ticker"]


# class InstrumentsRetrieveView(generics.RetrieveAPIView):
#     queryset = Instrument.objects.all()
#     serializer_class = InstrumentDetailSerializer
#     lookup_field = "ticker"
#
#     def get_object(self):
#         uppercase_ticker = self.kwargs.get(self.lookup_field, "").upper()
#         return generics.get_object_or_404(
#             self.get_queryset(), **{self.lookup_field: uppercase_ticker}
#         )