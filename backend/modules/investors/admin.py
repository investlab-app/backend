from django.contrib import admin

from modules.investors.models import Investor


@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ["id", "clerk_id"]
