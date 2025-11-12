from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class InstrumentsConfig(AppConfig):
    name = "modules.instruments"
    verbose_name = _("Instruments")
