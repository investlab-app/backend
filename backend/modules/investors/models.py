from django.db import models
from django.utils.translation import gettext_lazy as _
from modules.instruments.models import Instrument

class Investor(models.Model):
    clerk_id = models.CharField(unique=True, max_length=255, verbose_name=_("Clerk ID"))
    watching_instruments = models.ManyToManyField(Instrument, blank=True)

    def __str__(self):
        return f"Investor: {self.clerk_id}"
