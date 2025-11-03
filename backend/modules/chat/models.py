from django.db import models
from django.utils.translation import gettext_lazy as _

from modules.core.models import BaseModel
from modules.core.utils import get_local_datetime
from modules.investors.models import Investor


class ChatMessage(BaseModel):
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"

    ROLE_CHOICES = [
        (ROLE_USER, _("User")),
        (ROLE_ASSISTANT, _("Assistant")),
    ]

    investor = models.ForeignKey(
        Investor,
        on_delete=models.CASCADE,
        related_name="chat_messages",
        verbose_name=_("Investor"),
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        verbose_name=_("Role"),
    )
    content = models.TextField(
        verbose_name=_("Content"),
    )
    timestamp = models.DateTimeField(
        default=get_local_datetime,
        verbose_name=_("Timestamp"),
    )

    class Meta:
        verbose_name = _("Chat Message")
        verbose_name_plural = _("Chat Messages")
        ordering = ["timestamp"]

    def __str__(self):
        return f"Chat Message from {self.role} at {self.timestamp}"
