from django.contrib import admin

from unfold.admin import ModelAdmin
from modules.instruments_v3.models import Instrument


@admin.register(Instrument)
class UserAdmin(ModelAdmin):
    pass
