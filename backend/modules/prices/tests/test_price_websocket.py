import json
from unittest.mock import MagicMock

import pytest
from channels.layers import get_channel_layer
from channels.testing import ApplicationCommunicator, WebsocketCommunicator

from modules.prices.consumers import PriceStreamConsumer


def _get_websocket_communicator(user, ticker_names=""):
    scope = {"user": user, "url_route": {"kwargs": {"name": ticker_names}}}

    communicator = WebsocketCommunicator(
        PriceStreamConsumer.as_asgi(), f"/ws/prices/{ticker_names}/"
    )
    communicator.scope.update(scope)
    return communicator


async def _get_layer():
    layer = get_channel_layer()
    await layer.group_add("tickers_broadcast", "broadcast")
    return layer


async def _send_ticker_data(layer, msg):
    await layer.group_send(
        "tickers_broadcast", {"type": "broadcast.receive", "data": msg}
    )


async def _get_connected_communicator(ticker_names=""):
    user = MagicMock(is_authenticated=True)
    communicator = _get_websocket_communicator(user, ticker_names)
    connected, _ = await communicator.connect()
    assert connected
    return communicator


async def _assert_communicator_output(communicator, expected_output):
    output = await communicator.receive_output()
    output = json.loads(output["text"])
    assert output == expected_output


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
    assert connected is False


@pytest.mark.asyncio
async def test_single_ticker():
    communicator = await _get_connected_communicator("AAPL")
    await communicator.receive_nothing()

    layer = await _get_layer()
    await _send_ticker_data(
        layer, {"AAPL": "some_data", "XYZ": "other_data", "ABC": "more_data"}
    )

    await _assert_communicator_output(communicator, {"message": ["some_data"]})
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_multiple_tickers():
    communicator = await _get_connected_communicator("AAPL,ABC")
    await communicator.receive_nothing()

    layer = await _get_layer()
    await _send_ticker_data(
        layer, {"AAPL": "some_data", "XYZ": "other_data", "ABC": "more_data"}
    )

    await _assert_communicator_output(
        communicator, {"message": ["some_data", "more_data"]}
    )
    await communicator.disconnect()
