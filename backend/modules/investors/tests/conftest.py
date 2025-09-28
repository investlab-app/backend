import pytest
from faker import Faker

from modules.instruments.tests.conftest import (
    create_fake_instrument,
    instruments_factory,
)
from modules.investors.models import Asset, Investor

fake = Faker()


def create_fake_investor(clerk_id=None, balance=None, save=False):  # noqa: FBT002
    clerk_id = clerk_id or fake.pystr()
    if balance is None:
        balance = fake.pydecimal(15, 2, positive=True, max_value=100)

    investor = Investor(
        clerk_id=clerk_id,
        balance=balance,
    )
    if save:
        investor.save()
    return investor


@pytest.fixture
def investor_factory():
    def create_investor(**kwargs):
        return create_fake_investor(**kwargs, save=True)

    return create_investor


def create_fake_asset(
    investor=None,
    ticker=None,
    volume=None,
    save=False,  # noqa: FBT002
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
def asset_factory():
    def create_asset(**kwargs):
        return create_fake_asset(**kwargs, save=True)

    return create_asset
