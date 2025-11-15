from django.db import models
from django.utils.translation import gettext_lazy as _

from modules.core.models import BaseModel
from modules.investors.models import Investor


class Chat(BaseModel):
    investor = models.ForeignKey(
        Investor,
        on_delete=models.CASCADE,
        related_name="chats",
        verbose_name=_("Investor"),
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_("Title"),
    )

    class Meta:
        verbose_name = _("Chat")
        verbose_name_plural = _("Chats")
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Chat '{self.title}' for {self.investor}"

    @property
    def messages(self):
        return ChatMessage.objects.filter(chat=self).order_by("created_at")


class ChatMessage(BaseModel):
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="messages",
        verbose_name=_("Chat"),
    )
    message_list = models.BinaryField(
        verbose_name=_("Message List"),
    )

    class Meta:
        verbose_name = _("Chat Message")
        verbose_name_plural = _("Chat Messages")
        ordering = ["updated_at"]

    def __str__(self):
        return f"Chat Message from {self.chat} created at {self.created_at}"
