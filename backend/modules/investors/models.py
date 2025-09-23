from django.db import models
from django.utils.translation import gettext_lazy as _

from modules.core.models import BaseModel


class Investor(BaseModel):
    clerk_id = models.CharField(unique=True, max_length=255, verbose_name=_("Clerk ID"))
    language = models.CharField(
        max_length=10,
        default="en",
        verbose_name=_("Language"),
        help_text=_("User's preferred language (e.g., 'en', 'pl')"),
    )

    def __str__(self):
        return f"Investor {self.id} (Clerk ID: {self.clerk_id})"
