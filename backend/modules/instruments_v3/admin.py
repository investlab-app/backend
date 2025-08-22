from django.contrib import admin

from unfold.admin import ModelAdmin
from modules.instruments_v3.models import Ticker


@admin.register(Ticker)
class UserAdmin(ModelAdmin):
    pass
