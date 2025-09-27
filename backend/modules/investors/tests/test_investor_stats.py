import pytest
from faker import Faker
from django.urls import reverse

from modules.investors.models import Investor
from modules.core.tests.conftest import api_client, api_client_auth
from modules.transactions.models import Transaction
from modules.instruments.tests.conftest import instruments_factory

fake = Faker()
pytestmark = pytest.mark.django_db


def create_fake_investor(clerk_id=None, balance=None):
    clerk_id = clerk_id or fake.pystr()
    if balance is None:
        balance = fake.pydecimal(15, 2, True, max_value=100)

    return Investor(
        clerk_id=clerk_id,
        balance=balance,
    )


@pytest.fixture
def investor_factory(**kwargs):
    def create_investor():
        investor = create_fake_investor(**kwargs)
        investor.save()
        return investor

    return create_investor
