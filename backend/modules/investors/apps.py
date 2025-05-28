from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class InvestorsConfig(AppConfig):
    name = "modules.investors"
    verbose_name = _("Investors")
