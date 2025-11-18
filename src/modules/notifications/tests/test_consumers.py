import json
import random
import time
from unittest.mock import MagicMock

import pytest
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator

from modules.notifications.consumers import Websocket
from modules.prices.constants import PRICES_CHANNEL_LAYER
from modules.prices.management.commands.mock_stream_prices import PriceStreamMock


@pytest.fixture
async def communicator():
    user = MagicMock(is_authenticated=True)
    communicator = _get_websocket_communicator(user)
    _, _ = await communicator.connect()
    yield communicator
    await communicator.disconnect()


@pytest.fixture
async def layer():
    layer = get_channel_layer()
    await layer.group_add(PRICES_CHANNEL_LAYER, "broadcast")
    return layer


def _get_websocket_communicator(user, tickers=""):
    scope = {"user": user, "url_route": {"kwargs": {"names": tickers}}}

    communicator = WebsocketCommunicator(Websocket.as_asgi(), f"/ws/{tickers}")
    communicator.scope.update(scope)
    return communicator


def get_random_ohlc(ticker: str) -> dict:
    now_ms = int(time.time() * 1000)
    return {
        "symbol": ticker,
        "volume": random.randint(1000, 10000),
        "accumulated_volume": random.randint(1_000_000, 10_000_000),
        "official_open_price": round(op := random.uniform(0.4, 1.0), 4),
        "vwap": round(vw := (op + random.uniform(-0.01, 0.01)), 4),
        "open": round(o := (vw + random.uniform(-0.002, 0.002)), 4),
        "close": round(c := (vw + random.uniform(-0.002, 0.002)), 4),
        "high": round(max(o, c) + random.uniform(0, 0.002), 4),
        "low": round(min(o, c) - random.uniform(0, 0.002), 4),
        "aggregate_vwap": round(op + random.uniform(-0.02, 0.02), 4),
        "average_size": random.randint(100, 1000),
        "start_timestamp": now_ms - 1000,
        "end_timestamp": now_ms,
    }


def _create_ticker_data(*tickers: str) -> dict:
    return {ticker: get_random_ohlc(ticker) for ticker in tickers}


async def _send_ticker_data(layer, msg):
    await layer.group_send(PRICES_CHANNEL_LAYER, {"type": "send.prices", "data": msg})


async def _get_communicator_output(communicator):
    output = await communicator.receive_output()
    return json.loads(output["text"])


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_successful_connection():
    user = MagicMock(is_authenticated=True)
    communicator = _get_websocket_communicator(user)
    connected, _ = await communicator.connect()
    assert connected
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_failed_connection():
    user = MagicMock(is_authenticated=False)
    communicator = _get_websocket_communicator(user)
    connected, _ = await communicator.connect()
    msg = await communicator.receive_output(None)
    assert msg == {"type": "websocket.close"}
    await communicator.disconnect()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_no_subscriptions(communicator, layer):
    await _send_ticker_data(layer, _create_ticker_data("AAPL", "XYZ", "ABC"))

    assert await communicator.receive_nothing()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_empty_subscription(communicator, layer):
    await communicator.send_json_to({"type": "set_subscription", "subscriptions": []})

    await _send_ticker_data(layer, _create_ticker_data("AAPL", "XYZ", "ABC"))

    assert await communicator.receive_nothing()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_single_subscription(communicator, layer):
    await communicator.send_json_to(
        {"type": "set_subscription", "subscriptions": ["AAPL"]}
    )

    ticker_data = _create_ticker_data("AAPL", "XYZ", "ABC")
    await _send_ticker_data(layer, ticker_data)

    output = await _get_communicator_output(communicator)
    assert output["data"][0] == ticker_data["AAPL"]


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_multi_subscription(communicator, layer):
    await communicator.send_json_to(
        {"type": "set_subscription", "subscriptions": ["AAPL", "ABC"]}
    )

    ticker_data = _create_ticker_data("AAPL", "XYZ", "ABC")
    await _send_ticker_data(layer, ticker_data)

    output = await _get_communicator_output(communicator)
    assert len(output["data"]) == 2
    assert output["data"][0] == ticker_data["AAPL"]
    assert output["data"][1] == ticker_data["ABC"]


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_resubscription(communicator, layer):
    await communicator.send_json_to(
        {"type": "set_subscription", "subscriptions": ["AAPL", "ABC"]}
    )
    await communicator.send_json_to(
        {"type": "set_subscription", "subscriptions": ["XYZ", "ABC"]}
    )
    ticker_data = _create_ticker_data("AAPL", "XYZ", "ABC")
    await _send_ticker_data(layer, ticker_data)

    output = await _get_communicator_output(communicator)
    assert len(output["data"]) == 2
    assert output["data"][0] == ticker_data["XYZ"]
    assert output["data"][1] == ticker_data["ABC"]


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_does_not_send_empty_msgs(communicator, layer):
    await communicator.send_json_to(
        {"type": "set_subscription", "subscriptions": ["AAPL", "ABC"]}
    )

    await _send_ticker_data(layer, _create_ticker_data("XYZ"))

    assert await communicator.receive_nothing()


@pytest.mark.asyncio
@pytest.mark.django_db
async def test_tickers_in_query_params(layer):
    communicator = _get_websocket_communicator(
        MagicMock(is_authenticated=True), "AAPL,ABC"
    )
    await communicator.connect()

    ticker_data = _create_ticker_data("AAPL", "XYZ", "ABC")
    await _send_ticker_data(layer, ticker_data)

    output = await _get_communicator_output(communicator)
    assert len(output["data"]) == 2
    assert output["data"][0] == ticker_data["AAPL"]
    assert output["data"][1] == ticker_data["ABC"]
    await communicator.disconnect()
