from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from modules.core.models import BaseModel
from modules.instruments.models import Instrument
from modules.investors.models import Investor


class Graph(BaseModel):
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=False)
    raw_graph_data = models.JSONField()
    graph_data = models.JSONField()
    active = models.BooleanField(default=True)
    repeat = models.BooleanField(default=False)


class GraphEffect(BaseModel):
    graph = models.ForeignKey(Graph, on_delete=models.CASCADE)
    success = models.BooleanField()

    effect_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
    )
    effect_id = models.UUIDField()
    effect = GenericForeignKey("effect_type", "effect_id")


class BuySellEffect(BaseModel):
    instrument = models.ForeignKey(Instrument, on_delete=models.CASCADE)
    is_buy = models.BooleanField()
    amount = models.DecimalField(max_digits=30, decimal_places=15)
    action_price = models.DecimalField(max_digits=30, decimal_places=15)


class NotificationEffect(BaseModel):
    PUSH = "push"
    MAIL = "mail"

    message = models.TextField()
    format = models.CharField(choices={PUSH: "push", MAIL: "mail"})
