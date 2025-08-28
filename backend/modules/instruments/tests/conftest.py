import random

import pytest
from faker import Faker

from modules.instruments.constants import LocaleChoices, MarketChoices
from modules.instruments.models import Instrument
from modules.users.tests.conftest import user  # noqa: F401

fake = Faker()


def create_fake_instrument(
    ticker=None,
    name=None,
    market=None,
    locale=None,
    active=None,
    **kwargs,
):
    ticker = (ticker or str(fake.uuid4()[:20])).upper()
    name = name or fake.company()
    market = market or MarketChoices.STOCKS
    locale = locale or random.choice(LocaleChoices.choices)[0]
    active = active if active is not None else True

    return Instrument(
        ticker=ticker,
        name=name,
        market=market,
        locale=locale,
        active=active,
        **kwargs,
    )


@pytest.fixture
def instruments_factory():
    def create_instrument(**kwargs):
        instance = create_fake_instrument(**kwargs)
        instance.save()
        return instance

    return create_instrument
