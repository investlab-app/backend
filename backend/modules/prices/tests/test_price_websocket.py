import json
from unittest.mock import MagicMock

import pytest
from channels.layers import get_channel_layer
from channels.testing import WebsocketCommunicator

from modules.prices.constants import PRICES_CHANNEL_LAYER
from modules.prices.consumers import PriceStreamConsumer


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

    communicator = WebsocketCommunicator(
        PriceStreamConsumer.as_asgi(), f"/ws/prices/{tickers}"
    )
    communicator.scope.update(scope)
    return communicator


async def _send_ticker_data(layer, msg):
    await layer.group_send(
        PRICES_CHANNEL_LAYER, {"type": "broadcast.receive", "data": msg}
    )


async def _get_communicator_output(communicator):
    output = await communicator.receive_output()
    return json.loads(output["text"])


@pytest.mark.asyncio
async def test_successful_connection():
    user = MagicMock(is_authenticated=True)
    communicator = _get_websocket_communicator(user)
    connected, _ = await communicator.connect()
    assert connected
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_failed_connection():
    user = MagicMock(is_authenticated=False)
    communicator = _get_websocket_communicator(user)
    connected, _ = await communicator.connect()
    msg = await communicator.receive_output(None)
    assert msg == {'type': 'websocket.close'}
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_no_subscriptions(communicator, layer):
    await _send_ticker_data(layer, {"AAPL": "XXXX", "XYZ": "YYYY", "ABC": "ZZZZ"})

    assert await communicator.receive_nothing()


@pytest.mark.asyncio
async def test_empty_subscription(communicator, layer):
    await communicator.send_to(text_data=json.dumps({"set_subscription": []}))

    await _send_ticker_data(layer, {"AAPL": "XXXX", "XYZ": "YYYY", "ABC": "ZZZZ"})

    assert await communicator.receive_nothing()


@pytest.mark.asyncio
async def test_single_subscription(communicator, layer):
    await communicator.send_to(text_data=json.dumps({"set_subscription": ["AAPL"]}))

    await _send_ticker_data(layer, {"AAPL": "XXXX", "XYZ": "YYYY", "ABC": "ZZZZ"})

    output = await _get_communicator_output(communicator)
    assert output == {"prices": ["XXXX"]}


@pytest.mark.asyncio
async def test_multi_subscription(communicator, layer):
    await communicator.send_to(
        text_data=json.dumps({"set_subscription": ["AAPL", "ABC"]})
    )

    await _send_ticker_data(layer, {"AAPL": "XXXX", "XYZ": "YYYY", "ABC": "ZZZZ"})

    output = await _get_communicator_output(communicator)
    assert output == {"prices": ["XXXX", "ZZZZ"]}


@pytest.mark.asyncio
async def test_resubscription(communicator, layer):
    await communicator.send_to(
        text_data=json.dumps({"set_subscription": ["AAPL", "ABC"]})
    )
    await communicator.send_to(
        text_data=json.dumps({"set_subscription": ["XYZ", "ABC"]})
    )

    await _send_ticker_data(layer, {"AAPL": "XXXX", "XYZ": "YYYY", "ABC": "ZZZZ"})

    output = await _get_communicator_output(communicator)
    assert output == {"prices": ["YYYY", "ZZZZ"]}


@pytest.mark.asyncio
async def test_does_not_send_empty_msgs(communicator, layer):
    await communicator.send_to(
        text_data=json.dumps({"set_subscription": ["AAPL", "ABC"]})
    )

    await _send_ticker_data(layer, {"XYZ": "YYYY"})

    assert communicator.receive_nothing()


@pytest.mark.asyncio
async def test_tickers_in_query_params(layer):
    communicator = _get_websocket_communicator(
        MagicMock(is_authenticated=True), "AAPL,ABC"
    )
    await communicator.connect()

    await _send_ticker_data(layer, {"AAPL": "XXXX", "XYZ": "YYYY", "ABC": "ZZZZ"})

    output = await _get_communicator_output(communicator)
    assert output == {"prices": ["XXXX", "ZZZZ"]}
