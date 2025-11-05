from django.db import models

from modules.core.models import BaseModel
from modules.investors.models import Investor


class Graph(BaseModel):
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, blank=False)
    raw_graph_data = models.JSONField()
    graph_data = models.JSONField()
