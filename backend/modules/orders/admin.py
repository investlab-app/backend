from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from modules.orders.models import MarketOrder, Order


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ["id", "ticker", "investor", "detail_type"]
    list_filter = ["ticker", "investor", "detail_type"]
    search_fields = ("id", "investor__clerk_id", "ticker__ticker", "detail_id")
    ordering = ("-created_at",)
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (None, {"fields": ("id", "ticker", "investor")}),
        (_("Detail"), {"fields": ("detail_type", "detail_id")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description=_("Detail"))
    def detail_repr(self, obj):
        return str(obj.detail) if obj.detail else "-"


@admin.register(MarketOrder)
class MarketOrderAdmin(ModelAdmin):
    list_display = ["id", "volume", "volume_processed", "is_buy"]
    list_filter = ["is_buy"]
    search_fields = ("id",)
    ordering = ("-created_at",)
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (None, {"fields": ("id", "volume", "volume_processed", "is_buy")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )
