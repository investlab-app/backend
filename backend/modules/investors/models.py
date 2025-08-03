from django.db import models


class Investor(models.Model):
    user = models.OneToOneField("users.User", on_delete=models.CASCADE)
    watching_instruments = models.ManyToManyField("instruments.InstrumentV2", blank=True)

    def __str__(self):
        return f"Investor: {self.user.email}"
