from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class TransactionsConfig(AppConfig):
    name = "modules.transactions"
    verbose_name = _("Transactions")
