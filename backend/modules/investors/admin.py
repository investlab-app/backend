from django.contrib import admin

from modules.investors.models import Investor


@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ["clerk_id", "exp", "watching_instruments_count"]

    filter_horizontal = ["watching_instruments"]

    @admin.display(description="Watching Count")
    def watching_instruments_count(self, obj):
        return obj.watching_instruments.count()
