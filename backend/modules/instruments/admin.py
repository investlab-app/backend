from django.contrib import admin
from unfold.admin import ModelAdmin
from django.utils.translation import gettext_lazy as _
from modules.instruments.models import Instrument, CompanyDetails, IndexDetails


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
    search_fields = ("id,", "ticker", "name")
    readonly_fields = ("id", "created_at", "updated_at", "details")
    ordering = ("ticker",)
    fieldsets = (
        (
            None, {
                "fields": (
                    "id",
                    "ticker",
                    "type",
                    "name",
                    "currency",
                )
            }
        ),
        (
            _("Details"),
            {"fields": ("details_type", "details_id", "details",)},
        ),
        (
            _("Description"),
            {"fields": ("description",)},
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at")},
        ),
    )


@admin.register(CompanyDetails)
class CompanyDetailsAdmin(ModelAdmin):
    list_display = (
        "name",
        "country",
        "industry",
        "created_at",
        "updated_at",
    )
    search_fields = ("id", "name")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("name",)
    fieldsets = (
        (None, {"fields": ("id", "name")}),
        (
            _("Details"),
            {"fields": ("country", "industry", "website")},
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at")},
        ),
    )


@admin.register(IndexDetails)
class IndexDetailsAdmin(ModelAdmin):
    list_display = (
        "name",
        "fund_name",
        "created_at",
        "updated_at",
    )
    search_fields = ("id", "name")
    readonly_fields = ("id", "created_at", "updated_at")
    ordering = ("name",)
    fieldsets = (
        (None, {"fields": ("id", "name")}),
        (
            _("Details"),
            {"fields": ("fund_name",)},
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at")},
        ),
    )
