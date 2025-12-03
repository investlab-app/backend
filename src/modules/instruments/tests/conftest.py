import random

import pytest
from faker import Faker

from modules.authentication.tests.conftest import user
from modules.instruments.constants import LocaleChoices, MarketChoices
from modules.instruments.models import Instrument

fake = Faker()


def create_fake_instrument(
    ticker=None,
    name=None,
    market=None,
    locale=None,
    active=None,
    *,
    save=False,
    **kwargs,
):
    ticker = (ticker or str(fake.uuid4()[:20])).upper()
    name = name or fake.company()
    market = market or MarketChoices.STOCKS
    locale = locale or random.choice(LocaleChoices.choices)[0]
    active = active if active is not None else True

    instrument, created = Instrument.objects.get_or_create(
        ticker=ticker,
        defaults={
            "name": name,
            "market": market,
            "locale": locale,
            "active": active,
            **kwargs,
        },
    )
    if save and not created:
        instrument.save()

    return instrument


@pytest.fixture
def instruments_factory():
    def create_instrument(**kwargs):
        instance = create_fake_instrument(**kwargs)
        instance.save()
        return instance

    return create_instrument
