from django.contrib import admin

from modules.investors.models import Investor


@admin.register(Investor)
class InvestorAdmin(admin.ModelAdmin):
    list_display = ["id",  "watching_instruments_count"]
    # list_filter = ["user__clerk_role"]
    # search_fields = ["user__email", "user__first_name", "user__last_name"]
    filter_horizontal = ["watching_instruments"]

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "Email"  # type: ignore[attr-defined]

    def watching_instruments_count(self, obj):
        return obj.watching_instruments.count()

    watching_instruments_count.short_description = "Watching Count"  # type: ignore[attr-defined]
