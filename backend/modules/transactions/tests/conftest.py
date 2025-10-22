import pytest
from faker import Faker

from modules.transactions.models import Transaction

fake = Faker()


def create_fake_transaction(
    investor,
    ticker,
    volume=None,
    price=None,
    is_buy=None,
    date=None,
):
    if volume is None:
        volume = fake.pydecimal(positive=True, max_value=1e10)
    if price is None:
        price = fake.pydecimal(positive=True, max_value=1e10)
    if is_buy is None:
        is_buy = fake.pybool()
    t = Transaction(
        investor=investor,
        ticker=ticker,
        volume=volume,
        price=price,
        is_buy=is_buy,
    )
    if date:
        t.timestamp = date
    return t


@pytest.fixture
def transaction_factory():
    def create_transaction(**kwargs):
        t = create_fake_transaction(**kwargs)  # ty: ignore[missing-argument]
        t.save()
        return t

    return create_transaction
