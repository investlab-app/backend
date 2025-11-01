from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class GraphLangConfig(AppConfig):
    name = "modules.graph_lang"
    verbose_name = _("Graph Language")