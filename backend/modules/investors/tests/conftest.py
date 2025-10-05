import uuid
from decimal import Decimal

import pytest
from faker import Faker

from modules.instruments.tests.conftest import (
    create_fake_instrument,
    instruments_factory,
)
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


def create_fake_asset(
    investor=None,
    ticker=None,
    volume=Decimal(0),
    *,
    save=False,
):
    if investor is None:
        investor = create_fake_investor(save=save)
    if ticker is None:
        ticker = create_fake_instrument()
        if save:
            ticker.save()
    if volume is None:
        volume = fake.pydecimal(positive=True, max_value=1e10)

    asset = Asset(investor=investor, ticker=ticker, volume=volume)
    if save:
        asset.save()
    return asset


@pytest.fixture
def investor_factory():
    def create_investor(**kwargs):
        return create_fake_investor(**kwargs, save=True)

    return create_investor


@pytest.fixture
def asset_factory():
    def create_asset(**kwargs):
        return create_fake_asset(**kwargs, save=True)

    return create_asset
