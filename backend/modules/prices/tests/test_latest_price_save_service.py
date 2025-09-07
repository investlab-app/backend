from dataclasses import dataclass
import asyncio

import pytest
from channels.layers import get_channel_layer
from channels.db import database_sync_to_async

from modules.prices.constants import PRICES_CHANNEL_LAYER
from modules.prices.models import LatestPrice
from modules.prices.services import LatestPriceSaveService


@dataclass
class LatestPriceData:
    ticker :str
    price :float

    def __eq__(self, value):
        if not isinstance(value, LatestPrice): return

        return \
            self.ticker == value.ticker and \
            self.price == value.price


@pytest.fixture
async def layer():
    layer = get_channel_layer()
    await layer.group_add(PRICES_CHANNEL_LAYER, "broadcast")
    return layer

@pytest.fixture
async def price_service():
    future = asyncio.ensure_future(LatestPriceSaveService().run())
    yield future
    future.cancel()


async def _send_ticker_data(layer, msg):
    await layer.group_send(
        PRICES_CHANNEL_LAYER, {"type": "broadcast.receive", "data": msg}
    )

async def _run_test(data_sent, expected_result, layer):
    await _send_ticker_data(layer, data_sent)
    await asyncio.sleep(0.1)
    prices = await database_sync_to_async(lambda: LatestPrice.objects.all())()
    prices == expected_result

@pytest.mark.asyncio
@pytest.mark.django_db
async def test_no_data_sent__no_data_saved(layer, price_service):
    await _run_test({}, [], layer)

@pytest.mark.asyncio
@pytest.mark.django_db
async def test_single_ticker_sent__single_ticker_saved(layer, price_service):
    data = {
        "AAPL": {
            "low": 2,
            "high": 8
        }
    }
    result = [
        LatestPriceData("AAPL", 5)
    ]
    await _run_test(data, result, layer)

@pytest.mark.asyncio
@pytest.mark.django_db
async def test_multiple_tickers_sent__all_saved(layer, price_service):
    data = {
        "AAPL": {
            "low": 2,
            "high": 8
        },
        "OTHER": {
            "low": 20,
            "high": 22,
        }
    }
    result = [
        LatestPriceData("AAPL", 5),
        LatestPriceData("OTHER", 21),
    ]
    await _run_test(data, result, layer)