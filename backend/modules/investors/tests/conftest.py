import uuid
from decimal import Decimal

import pytest
from faker import Faker

from modules.investors.models import Asset, Investor

fake = Faker()


def create_fake_investor(
    investor_id=None, clerk_id=None, balance=Decimal(0), *, save=False
):
    if investor_id is None:
        investor_id = uuid.uuid4()
    if clerk_id is None:
        clerk_id = fake.pystr()

    investor = Investor(id=investor_id, clerk_id=clerk_id, balance=balance)
    if save:
        investor.save()
    return investor


def fake_asset(investor=None, ticker=None, volume=Decimal(0), *, save=False):
    asset = Asset(investor=investor, ticker=ticker, volume=volume)
    if save:
        asset.save()
    return asset


@pytest.fixture
def investor_factory():
    """Factory fixture for creating investors in tests."""

    def create_investor(**kwargs):
        return create_fake_investor(**kwargs, save=True)

    return create_investor
