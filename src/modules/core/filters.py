from django.db.models import F
from rest_framework.filters import OrderingFilter


class NullsLastOrderingFilter(OrderingFilter):
    def filter_queryset(self, request, queryset, view):
        ordering = self.get_ordering(request, queryset, view)
        if not ordering:
            return queryset

        corrected = []
        for field in ordering:
            if field.startswith("-"):
                corrected.append(F(field[1:]).desc(nulls_last=True))
            else:
                corrected.append(F(field).asc(nulls_last=True))

        return queryset.order_by(*corrected)
