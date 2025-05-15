from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as _GroupAdmin
from django.contrib.auth.admin import UserAdmin as _UserAdmin
from django.contrib.auth.models import Group as _Group
from django.utils.translation import gettext_lazy as _
from modules.users.models import Group, User

admin.site.unregister(_Group)


@admin.register(Group)
class GroupAdmin(_GroupAdmin):
    pass


@admin.register(User)
class UserAdmin(_UserAdmin):
    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    # "groups",
                    # "user_permissions",
                ),
            },
        ),
        (
            _("Timestamps"),
            {"fields": ("last_login", "date_joined", "created_at", "updated_at")},
        ),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                    # "groups", "user_permissions"
                ),
            },
        ),
    )
    readonly_fields = ("id", "created_at", "updated_at", "last_login", "date_joined")
    ordering = ("-updated_at", "-created_at")
    list_display = ("email", "is_staff", "is_active", "updated_at")
    list_filter = ("is_staff", "is_active")
    search_fields = ("email", "id")
