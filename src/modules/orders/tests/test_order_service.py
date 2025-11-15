from decimal import Decimal

import pytest

from modules.investors.tests.conftest import (
    asset_factory,
    create_fake_asset,
    create_fake_investor,
)
from modules.orders.models import Order
from modules.orders.services.order_services import OrderService
from modules.orders.tests.conftest import fake_limit_order, fake_market_order

pytestmark = pytest.mark.django_db


def test_create_market_sell_insufficient_due_to_blocked(asset_factory):
    asset = asset_factory(volume=Decimal(5))
    investor = asset.investor
    instrument = asset.ticker

    # existing sell order blocking 3 units
    fake_market_order(
        investor=investor,
        ticker=instrument,
        is_buy=False,
        volume=Decimal(3),
        save=True,
    )

    svc = OrderService()
    order = svc.create_market(
        investor=investor, instrument=instrument, volume=Decimal(3), is_buy=False
    )
    assert order is None
    # only the existing order should be present
    assert Order.objects.filter(investor=investor).count() == 1


def test_create_market_sell_success_when_enough_available(asset_factory):
    asset = asset_factory(volume=Decimal(5))
    investor = asset.investor
    instrument = asset.ticker

    # existing sell order blocking 3 units
    fake_market_order(
        investor=investor,
        ticker=instrument,
        is_buy=False,
        volume=Decimal(3),
        save=True,
    )

    svc = OrderService()
    order = svc.create_market(
        investor=investor, instrument=instrument, volume=Decimal(2), is_buy=False
    )
    assert order is not None
    # existing + newly created
    assert Order.objects.filter(investor=investor).count() == 2


def test_create_limit_sell_respects_blocked_from_other_orders(asset_factory):
    asset = asset_factory(volume=Decimal(10))
    investor = asset.investor
    instrument = asset.ticker

    # Block 8 with two existing sell orders (5 + 3)
    fake_market_order(
        investor=investor,
        ticker=instrument,
        is_buy=False,
        volume=Decimal(5),
        save=True,
    )
    fake_limit_order(
        investor=investor,
        ticker=instrument,
        is_buy=False,
        volume=Decimal(3),
        save=True,
    )

    svc = OrderService()
    # trying to sell 3 more should fail (available = 10 - 8 = 2)
    order = svc.create_limit(
        investor=investor,
        instrument=instrument,
        volume=Decimal(3),
        is_buy=False,
        limit_price=Decimal(1),
    )
    assert order is None

    # selling 2 should succeed
    order2 = svc.create_limit(
        investor=investor,
        instrument=instrument,
        volume=Decimal(2),
        is_buy=False,
        limit_price=Decimal(1),
    )
    assert order2 is not None
