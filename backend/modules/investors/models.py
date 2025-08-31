from django.db import models
from django.utils.translation import gettext_lazy as _


class Investor(models.Model):
    # user = models.OneToOneField("users.User", on_delete=models.CASCADE)
    clerk_id = models.CharField(unique=True, max_length=255, verbose_name=_("Clerk ID"), null=True,
    blank=True)
    watching_instruments = models.ManyToManyField("instruments.Instrument", blank=True)

    def __str__(self):
        return f"Investor: {self.user.email}"
