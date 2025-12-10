from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from modules.transactions.models import Transaction


@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ["id", "ticker", "investor", "timestamp"]
    list_filter = ["ticker", "investor"]
    search_fields = ("id", "investor__clerk_id", "ticker__ticker")
    ordering = ("-timestamp",)
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (None, {"fields": ("id", "ticker", "investor", "timestamp")}),
        (_("Detail"), {"fields": ("volume", "price", "is_buy")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )
