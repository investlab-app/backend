import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_healthcheck(api_client):
    url = reverse("healthcheck")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json() == {"message": "App is running!"}


@pytest.mark.asyncio
async def test_websocket_healthcheck(websocket_communicator):
    """Test websocket connection and initial message"""
    communicator = await websocket_communicator()

    # Test connection
    connected, _ = await communicator.connect()
    assert connected

    # Test that we receive the initial connection message
    response = await communicator.receive_json_from()
    assert response == {"message": "Connection established"}

    # Test echo functionality
    test_message = {"message": "ping"}
    await communicator.send_json_to(test_message)

    echo_response = await communicator.receive_json_from()
    assert echo_response == {"message": "Echo: ping"}

    # Clean up
    await communicator.disconnect()


@pytest.mark.asyncio
async def test_websocket_healthcheck_with_auth(websocket_communicator_auth):
    """Test websocket connection with authenticated user"""
    communicator = await websocket_communicator_auth()

    # Test connection
    connected, _ = await communicator.connect()
    assert connected

    # Test that we receive the initial connection message
    response = await communicator.receive_json_from()
    assert response == {"message": "Connection established"}

    # Test echo functionality with a different message
    test_message = {"message": "authenticated ping"}
    await communicator.send_json_to(test_message)

    echo_response = await communicator.receive_json_from()
    assert echo_response == {"message": "Echo: authenticated ping"}

    # Clean up
    await communicator.disconnect()
