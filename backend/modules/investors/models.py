from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _


class Investor(models.Model):
    clerk_id = models.CharField(unique=True, max_length=255, verbose_name=_("Clerk ID"))
    exp = models.IntegerField(verbose_name=_("EXP"), default=0, validators=[MinValueValidator(0)])
    watching_instruments = models.ManyToManyField("instruments.Instrument", blank=True)

    def __str__(self):
        return f"Investor: {self.clerk_id}"
