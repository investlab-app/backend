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
from modules.investors.tests.conftest import create_fake_asset, create_fake_investor
from modules.orders.order_engine.structures import (
    EngineAsset,
    EngineOrderUpdate,
    EngineTransaction,
    MarketEngineOrder,
    TradeEngineInput,
    TradeEngineOutput,
)
from modules.orders.services.engine_services import (
    PricesFetcher,
    TradeEngineDataFetcher,
    TradeEngineOutputHandler,
)
from modules.orders.tests.conftest import fake_market_order, uuids
from modules.prices.constants import PRICES_CHANNEL_LAYER
from modules.transactions.schemas import TransactionParams

TEST_INVESTOR_ID = "816e3548-a012-412d-879a-cc742b58e721"
TEST_INVESTOR_ID_2 = "7f59dbfa-a79a-4d9f-9841-65d6598590f6"


@pytest.mark.django_db(transaction=True)
def test_trade_engine_data_fetcher(uuids):
    inv_1 = create_fake_investor(
        investor_id=TEST_INVESTOR_ID, balance=Decimal(40), save=True
    )
    inv_2 = create_fake_investor(
        investor_id=TEST_INVESTOR_ID_2, balance=Decimal(70), save=True
    )

    instrument_1 = create_fake_instrument(ticker="AAPL", save=True)
    instrument_2 = create_fake_instrument(ticker="OHT", save=True)

    create_fake_asset(
        investor=inv_1, ticker=instrument_1, volume=Decimal(10), save=True
    )
    create_fake_asset(
        investor=inv_1, ticker=instrument_2, volume=Decimal(40), save=True
    )

    fake_market_order(
        inv_1, instrument_1, order_id=uuids[0], is_buy=True, volume=3, save=True
    )
    fake_market_order(
        inv_2, instrument_1, order_id=uuids[1], is_buy=False, volume=5, save=True
    )

    result = TradeEngineDataFetcher().fetch()
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
            TEST_INVESTOR_ID: Decimal(40),
            TEST_INVESTOR_ID_2: Decimal(70),
        },
    )

    assert result == expected


@pytest.mark.django_db()
@patch("modules.orders.services.engine_services.ExecuteTransactionService.sell")
@patch("modules.orders.services.engine_services.ExecuteTransactionService.buy")
def test_trade_engine_output_handler(buy, sell, uuids):
    ticker = create_fake_instrument(ticker="AAPL", save=True)
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
        updated_orders=[EngineOrderUpdate(id=uuids[1], volume_processed=Decimal(5))],
        completed_orders=[uuids[2]],
    )
    prices = {"AAPL": 20}

    TradeEngineOutputHandler().handle(output=output, prices=prices)

    investor = Investor.objects.get(id=TEST_INVESTOR_ID)
    buy.assert_called_with(
        TransactionParams(
            investor=investor,
            ticker=ticker,
            volume=Decimal(5),
            action_price=Decimal(20),
        )
    )
    sell.assert_called_with(
        TransactionParams(
            investor=investor,
            ticker=ticker,
            volume=Decimal(15),
            action_price=Decimal(20),
        )
    )
