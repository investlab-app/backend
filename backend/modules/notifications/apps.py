from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class NotificationsConfig(AppConfig):
    name = "modules.notifications"
    verbose_name = _("Notifications")
