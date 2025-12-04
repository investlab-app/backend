from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from modules.transactions.models import Transaction, PartialTransaction


@admin.register(Transaction)
class TransactionAdmin(ModelAdmin):
    list_display = ["id", "ticker", "investor"]
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

@admin.register(PartialTransaction)
class PartialTransactionAdmin(ModelAdmin):
    list_display = ["id", "buy_transaction", "sell_transaction", "volume", "is_closed"]
    list_filter = ["buy_transaction__ticker", "buy_transaction__investor"]
    search_fields = ("buy_transaction__id", "sell_transaction__id", "buy_transaction__investor__clerk_id")
    ordering = ("-buy_transaction__timestamp",)
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (None, {"fields": ("id", "buy_transaction", "sell_transaction", "volume")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )
    
    def is_closed(self, obj):
        """Display whether the partial transaction is closed (has a sell transaction)."""
        return obj.sell_transaction is not None
    is_closed.boolean = True
    is_closed.short_description = _("Is Closed")
