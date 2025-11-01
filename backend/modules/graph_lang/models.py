from django.db import models

from modules.core.models import BaseModel
from modules.investors.models import Investor

class Graph(BaseModel):
    investor = models.ForeignKey(Investor, on_delete=models.CASCADE)
    raw_graph_data = models.TextField()
    graph_data = models.TextField()

