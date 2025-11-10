import pytest
import uuid
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal
from modules.graph_lang.framework.scheduler_updater import SchedulerUpdater
from modules.graph_lang.models import Graph
from modules.investors.tests.conftest import create_fake_investor

pytestmark = pytest.mark.django_db


def fake_graph(
    id=None, investor=None, raw_graph_data="", graph_data="", *, save=False
) -> Graph:
    investor = investor or create_fake_investor(save=save)
    id = id or uuid.uuid4()
    graph = Graph(
        id=id,
        investor=investor,
        raw_graph_data=raw_graph_data,
        graph_data=graph_data,
    )
    if save:
        graph.save()
    return graph
