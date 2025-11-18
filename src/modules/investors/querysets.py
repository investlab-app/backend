from datetime import timedelta

from django.db.models import QuerySet, Sum

from modules.core.utils import get_local_datetime


class DepositHistoryQuerySet(QuerySet):
    def deposited_last_24h(self):
        now = get_local_datetime()
        threshold = now - timedelta(hours=24)
        return self.filter(deposited_at__gt=threshold)

    def sum_amount(self):
        return self.aggregate(Sum("amount"))["amount__sum"]
