from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import Group as _Group
from django.db import models
from django.utils.translation import gettext_lazy as _
from modules.core.models import BaseModel
from modules.users.managers import UserManager


class User(BaseModel, AbstractUser):
    username = None
    email = models.EmailField(unique=True, verbose_name=_("Email"))

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return self.email


class Group(_Group):

    class Meta:
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
