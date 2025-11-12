import uuid
from decimal import Decimal

import pytest

from modules.instruments.tests.conftest import create_fake_instrument
from modules.orders.models import LimitOrder, MarketOrder, Order


@pytest.fixture
def uuids():
    return [uuid.uuid4() for i in range(10)]


def fake_market_order(
    investor=None,
    ticker=None,
    order_id=None,
    *,
    is_buy=True,
    volume=Decimal(0),
    volume_processed=Decimal(0),
    save=False,
) -> Order:
    if order_id is None:
        order_id = uuid.uuid4()
    if ticker is None:
        ticker = create_fake_instrument(save=save)

    order_det = MarketOrder(
        volume=volume, volume_processed=volume_processed, is_buy=is_buy
    )
    if save:
        order_det.save()
    order = Order(id=order_id, investor=investor, ticker=ticker, detail=order_det)
    if save:
        order.save()
    return order


def fake_limit_order(
    investor=None,
    ticker=None,
    order_id=None,
    *,
    is_buy=True,
    volume=Decimal(0),
    volume_processed=Decimal(0),
    limit_price=Decimal(0),
    save=False,
) -> Order:
    if order_id is None:
        order_id = uuid.uuid4()
    if ticker is None:
        ticker = create_fake_instrument(save=save)

    order_det = LimitOrder(
        volume=volume,
        volume_processed=volume_processed,
        is_buy=is_buy,
        limit_price=limit_price,
    )
    if save:
        order_det.save()
    order = Order(id=order_id, investor=investor, ticker=ticker, detail=order_det)
    if save:
        order.save()
    return order
