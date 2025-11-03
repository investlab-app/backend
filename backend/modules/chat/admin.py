from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from modules.chat.models import ChatMessage


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ("investor", "role", "timestamp", "preview")
    list_filter = ("role", "timestamp", "investor")
    search_fields = ("content", "investor__clerk_id")
    readonly_fields = ("id", "created_at", "updated_at", "timestamp")
    ordering = ("-timestamp",)

    fieldsets = (
        (
            _("Message"),
            {
                "fields": ("investor", "role", "content"),
            },
        ),
        (
            _("Metadata"),
            {
                "fields": ("timestamp", "id", "created_at", "updated_at"),
                "classes": ("collapse",),
            },
        ),
    )

    def preview(self, obj):
        """Show a preview of the message content."""
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content

    preview.short_description = _("Preview")
