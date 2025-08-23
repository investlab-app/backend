from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from unfold.admin import ModelAdmin
from modules.instruments_v3.models import Instrument


@admin.register(Instrument)
class InstrumentAdmin(ModelAdmin):
    list_display = (
        "ticker",
        "name",
        "market",
        "locale",
        "active",
        "currency_name",
        "primary_exchange",
        "last_updated_utc",
    )
    list_filter = (
        "active",
        "locale",
        "market",
        "type",
    )
    search_fields = (
        "ticker",
        "name",
        "cik",
        "composite_figi",
        "share_class_figi",
    )
    ordering = ("ticker",)

    readonly_fields = (
        "id",
        "ticker",
        "created_at",
        "updated_at",
        "last_updated_utc",
    )

    fieldsets = (
        (None, {
            "fields": (
                "id",
                "ticker",
                "name",
                "active",
                "type",
                "description",
                "homepage_url",
                "phone_number",
            )
        }),
        (_("Market Data"), {
            "fields": (
                "market",
                "locale",
                "market_cap",
                "currency_name",
                "currency_symbol",
                "base_currency_name",
                "base_currency_symbol",
                "source_feed",
            )
        }),
        (_("FIGI & Identifiers"), {
            "fields": (
                "cik",
                "composite_figi",
                "share_class_figi",
                "share_class_shares_outstanding",
                "weighted_shares_outstanding",
            )
        }),
        (_("Address Information"), {
            "classes": ("collapse",),
            "fields": (
                "address1",
                "address2",
                "city",
                "state",
                "country",
                "postal_code",
            )
        }),
        (_("Branding"), {
            "classes": ("collapse",),
            "fields": (
                "icon_url",
                "logo_url",
                "accent_color",
                "light_color",
                "dark_color",
            )
        }),
        (_("Extra Info"), {
            "classes": ("collapse",),
            "fields": (
                "sic_code",
                "sic_description",
                "total_employees",
                "ticker_root",
                "ticker_suffix",
                "list_date",
                "delisted_utc",
            )
        }),
        (
            _("Timestamps"),
            {"fields": ("last_updated_utc", "created_at", "updated_at")},
        ),
    )
