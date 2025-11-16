import pytest
from decimal import Decimal

from faker import Faker

from modules.graph_lang.framework.nodes import (
    PriceOfNode,
    MoneyAvailableNode,
    NumberOfAssetsNode,
    ValueOfAssetsNode
)
from modules.graph_lang.framework.nodes.node import ExecutionContext
from modules.graph_lang.tests.conftest_nodes import (
    PriceProviderMock,
)
from modules.investors.models import Asset
from modules.investors.tests.conftest import create_fake_investor
from modules.instruments.tests.conftest import create_fake_instrument

fake = Faker()



def test_price_of_node():
    dt = fake.date_time()
    price_provider = PriceProviderMock()
    price_provider.set("AAPL", dt, Decimal(10))

    node = PriceOfNode()
    node.ticker.set("AAPL")

    context = ExecutionContext(price_provider, set(), dt)

    assert node.out.get(context) == 10

@pytest.mark.django_db
def test_money_available_node():
    dt = fake.date_time()
    investor = create_fake_investor(balance=100)
    investor.blocked_funds = 50
    investor.save()

    node = MoneyAvailableNode()

    context = ExecutionContext(None, set(), dt, investor_id=investor.id)

    assert node.out.get(context) == 50


@pytest.mark.django_db
def test_number_of_assets_node():
    dt = fake.date_time()
    instrument = create_fake_instrument('AAPL', save=True)
    investor = create_fake_investor(save=True)
    Asset.objects.create(investor = investor, ticker = instrument, volume = 50)

    node = NumberOfAssetsNode()
    node.ticker.set('AAPL')

    context = ExecutionContext(None, set(), dt, investor_id=investor.id)

    assert node.out.get(context) == 50

@pytest.mark.django_db
def test_number_of_assets_node__no_assets__returns_0():
    dt = fake.date_time()
    create_fake_instrument('AAPL', save=True)
    investor = create_fake_investor(save=True)

    node = NumberOfAssetsNode()
    node.ticker.set('AAPL')

    context = ExecutionContext(None, set(), dt, investor_id=investor.id)

    assert node.out.get(context) == 0


@pytest.mark.django_db
def test_value_of_assets_node():
    dt = fake.date_time()
    instrument = create_fake_instrument('AAPL', save=True)
    investor = create_fake_investor(save=True)
    Asset.objects.create(investor = investor, ticker = instrument, volume = 50)
    price_provider = PriceProviderMock()
    price_provider.set('AAPL', dt, 2)

    node = ValueOfAssetsNode()
    node.ticker.set('AAPL')

    context = ExecutionContext(price_provider, set(), dt, investor_id=investor.id)

    assert node.out.get(context) == 100

@pytest.mark.django_db
def test_number_of_assets_node__no_assets__returns_0():
    dt = fake.date_time()
    create_fake_instrument('AAPL', save=True)
    investor = create_fake_investor(save=True)
    price_provider = PriceProviderMock()
    price_provider.set('AAPL', dt, 2)

    node = ValueOfAssetsNode()
    node.ticker.set('AAPL')

    context = ExecutionContext(price_provider, set(), dt, investor_id=investor.id)

    assert node.out.get(context) == 0

