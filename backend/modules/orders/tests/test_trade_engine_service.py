import asyncio
import uuid
from contextlib import suppress
from decimal import Decimal
from unittest.mock import patch

import pytest
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer

from modules.instruments.tests.conftest import create_fake_instrument
from modules.investors.models import Investor
from modules.investors.tests.conftest import create_fake_investor, fake_asset
from modules.orders.order_engine.structures import (
    EngineAsset,
    EngineTransaction,
    MarketEngineOrder,
    MarketEngineOrderUpdate,
    TradeEngineInput,
    TradeEngineOutput,
)
from modules.orders.services import (
    PricesFetcher,
    TradeEngineDataFetcher,
    TradeEngineOutputHandler,
)
from modules.orders.tests.conftest import fake_market_order, uuids
from modules.prices.constants import PRICES_CHANNEL_LAYER

TEST_INVESTOR_ID = "816e3548-a012-412d-879a-cc742b58e721"
TEST_INVESTOR_ID_2 = "7f59dbfa-a79a-4d9f-9841-65d6598590f6"


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
async def test_trade_engine_data_fetcher(uuids):
    def setup():
        inv_1 = create_fake_investor(
            investor_id=TEST_INVESTOR_ID, balance=Decimal(40), save=True
        )
        inv_2 = create_fake_investor(
            investor_id=TEST_INVESTOR_ID_2, balance=Decimal(70), save=True
        )

        instrument_1 = create_fake_instrument(ticker="AAPL", save=True)
        instrument_2 = create_fake_instrument(ticker="OHT", save=True)

        fake_asset(investor=inv_1, ticker=instrument_1, volume=Decimal(10), save=True)
        fake_asset(investor=inv_1, ticker=instrument_2, volume=Decimal(40), save=True)

        fake_market_order(
            inv_1, instrument_1, order_id=uuids[0], is_buy=True, volume=3, save=True
        )
        fake_market_order(
            inv_2, instrument_1, order_id=uuids[1], is_buy=False, volume=5, save=True
        )

    await database_sync_to_async(setup)()

    result = await TradeEngineDataFetcher().fetch()
    expected = TradeEngineInput(
        orders=[
            MarketEngineOrder(
                id=uuids[0],
                ticker="AAPL",
                investor_id=TEST_INVESTOR_ID,
                volume=Decimal(3),
                is_buy=True,
            ),
            MarketEngineOrder(
                id=uuids[1],
                ticker="AAPL",
                investor_id=TEST_INVESTOR_ID_2,
                volume=Decimal(5),
                is_buy=False,
            ),
        ],
        assets=[
            EngineAsset(
                investor_id=TEST_INVESTOR_ID, volume=Decimal(10), ticker="AAPL"
            ),
            EngineAsset(investor_id=TEST_INVESTOR_ID, volume=Decimal(40), ticker="OHT"),
        ],
        prices={},
        balances={
            TEST_INVESTOR_ID: Decimal("40.00"),
            TEST_INVESTOR_ID_2: Decimal("70.00"),
        },
    )

    assert result == expected


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
@patch("modules.orders.services.sell")
@patch("modules.orders.services.buy")
async def test_trade_engine_output_handler(buy, sell, uuids):
    ticker = create_fake_instrument(ticker="AAPL")

    def setup():
        ticker.save()
        inv = create_fake_investor(investor_id=TEST_INVESTOR_ID, save=True)

        fake_market_order(
            investor=inv, ticker=ticker, order_id=uuids[0], volume=Decimal(5), save=True
        )
        fake_market_order(
            investor=inv,
            ticker=ticker,
            order_id=uuids[1],
            volume=Decimal(10),
            save=True,
        )
        fake_market_order(
            investor=inv,
            ticker=ticker,
            order_id=uuids[2],
            volume=Decimal(15),
            save=True,
        )

    await database_sync_to_async(setup)()
    output = TradeEngineOutput(
        transactions=[
            EngineTransaction(
                ticker="AAPL",
                volume=Decimal(5),
                is_buy=True,
                investor_id=TEST_INVESTOR_ID,
            ),
            EngineTransaction(
                ticker="AAPL",
                volume=Decimal(15),
                is_buy=False,
                investor_id=TEST_INVESTOR_ID,
            ),
        ],
        updated_orders=[
            MarketEngineOrderUpdate(id=uuids[1], volume_processed=Decimal(5))
        ],
        completed_orders=[uuids[2]],
    )
    prices = {"AAPL": 20}

    await TradeEngineOutputHandler().handle(output=output, prices=prices)

    investor = await database_sync_to_async(Investor.objects.get)(id=TEST_INVESTOR_ID)
    buy.assert_called_with(
        investor=investor, ticker=ticker, volume=Decimal(5), action_price=20
    )
    sell.assert_called_with(
        investor=investor, ticker=ticker, volume=Decimal(15), action_price=20
    )


@pytest.mark.asyncio
async def test_prices_fetcher():
    fetcher = PricesFetcher()
    layer = get_channel_layer()

    run_task = asyncio.ensure_future(fetcher.run())

    await asyncio.sleep(0.1)
    mock_price_data = {
        "AAPL": {"high": "150.50", "low": "149.50"},
        "GOOG": {"high": "2800.00", "low": "2790.00"},
    }
    await layer.group_send(PRICES_CHANNEL_LAYER, {"data": mock_price_data})
    await asyncio.sleep(0.1)

    prices = fetcher.get_prices()
    assert prices["AAPL"] == Decimal("150.00")
    assert prices["GOOG"] == Decimal("2795.00")

    run_task.cancel()
    try:
        await run_task
    except asyncio.CancelledError:
        suppress(asyncio.CancelledError)
