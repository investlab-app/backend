from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from modules.investors.models import (
    AccountValueSnapshot,
    Asset,
    DepositHistory,
    Investor,
    NotificationHistory,
)


@admin.register(Investor)
class InvestorAdmin(ModelAdmin):
    list_display = ["clerk_id", "balance", "watching_instruments_count"]
    filter_horizontal = ["watching_instruments"]
    search_fields = ("id",)
    ordering = ("-balance",)
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (None, {"fields": ("id", "clerk_id", "balance", "blocked_funds")}),
        (_("Watching Instruments"), {"fields": ("watching_instruments",)}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )

    @admin.display(description="Watching Count")
    def watching_instruments_count(self, obj):
        return obj.watching_instruments.count()


@admin.register(Asset)
class AssetAdmin(ModelAdmin):
    list_display = ["investor", "ticker", "volume"]
    list_filter = ["ticker", "investor"]
    search_fields = ("investor__clerk_id", "ticker__ticker")
    ordering = ("-volume",)
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (None, {"fields": ("id", "investor", "ticker", "volume")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(AccountValueSnapshot)
class AccountValueSnapshotAdmin(ModelAdmin):
    list_display = ["investor", "value", "timestamp"]
    list_filter = ["investor"]
    search_fields = ("investor__clerk_id",)
    ordering = ("-timestamp",)
    readonly_fields = (
        "id",
        "created_at",
        "updated_at",
    )
    fieldsets = (
        (None, {"fields": ("id", "investor", "value", "timestamp")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(NotificationHistory)
class NotificationHistoryAdmin(ModelAdmin):
    list_display = ["investor", "type", "sent_at"]
    list_filter = ["type", "investor"]
    search_fields = ("investor__clerk_id", "type", "message_en", "message_pl")
    ordering = ("-sent_at",)
    readonly_fields = ("id", "sent_at", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("id", "investor", "type")}),
        (_("Messages"), {"fields": ("message_en", "message_pl")}),
        (_("Timestamps"), {"fields": ("sent_at", "created_at", "updated_at")}),
    )


@admin.register(DepositHistory)
class DepositHistoryAdmin(ModelAdmin):
    list_display = ["investor", "amount", "deposited_at"]
    list_filter = ["investor"]
    search_fields = ("investor__clerk_id",)
    ordering = ("-deposited_at",)
    readonly_fields = ("id", "deposited_at", "created_at", "updated_at")

    fieldsets = (
        (None, {"fields": ("id", "investor", "amount")}),
        (_("Timestamps"), {"fields": ("deposited_at", "created_at", "updated_at")}),
    )
