from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.translation import gettext_lazy as _
from modules.instruments.models import Instrument


@admin.register(Instrument)
class InstrumentAdmin(ModelAdmin):
    list_display = (
        "ticker",
        "type",
        "name",
        "currency",
        "created_at",
        "updated_at",
    )
    list_filter = ("type", "currency")
    search_fields = ("ticker", "name", "id")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("ticker",)
    fieldsets = (
        (None, {"fields": ("id", "ticker", "type", "name", "currency")}),
        (
            _("Description"),
            {"fields": ("description",)},
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at")},
        ),
    )
