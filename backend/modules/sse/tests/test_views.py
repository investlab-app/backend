import uuid
from unittest.mock import Mock, patch

import pytest
from django.http import HttpResponse
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIRequestFactory

from modules.core.tests.conftest import api_client_auth
from modules.sse import SSERequestParams
from modules.sse.views import SSESubscribeView, SSEUnsubscribeView
from modules.users.tests.conftest import user

pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_connection_id():
    return uuid.uuid4()


@pytest.fixture
def mock_symbols():
    return {"AAPL", "GOOGL"}


@pytest.fixture
def valid_request_data(mock_connection_id, mock_symbols):
    return {
        "connectionId": str(mock_connection_id),
        "symbols": list(mock_symbols),
    }


@pytest.fixture
def mock_parsed_params(mock_connection_id, mock_symbols):
    params = Mock(spec=SSERequestParams)
    params.connection_id = mock_connection_id
    params.symbols = mock_symbols
    return params


class TestSSESubscribeView:
    def test_subscribe_put_success(
        self,
        api_client_auth,
        valid_request_data,
        mock_parsed_params,
        mock_connection_id,
        mock_symbols,
    ):
        with (
            patch(
                "modules.sse.views.parse_sse_request",
                return_value=mock_parsed_params,
            ) as mock_parse,
            patch("modules.sse.views.subscribe") as mock_subscribe,
            patch("modules.sse.views.logging.debug") as mock_logging_debug,
        ):

            url = reverse("sse-subscribe")
            response = api_client_auth.put(url, valid_request_data, format="json")

            mock_parse.assert_called_once_with(valid_request_data)
            mock_subscribe.assert_called_once_with(mock_connection_id, mock_symbols)
            mock_logging_debug.assert_called_once_with(
                f"{mock_connection_id}: Subscribed to symbols: {mock_symbols}"
            )
            assert response.status_code == status.HTTP_200_OK
            assert isinstance(response, HttpResponse)
            assert (
                response.content.decode() == f"Subscribed to new events: {mock_symbols}"
            )

    def test_subscribe_put_invalid_data(self, api_client_auth):
        invalid_data = {"symbols": "AAPL"}  # Missing connectionId

        with patch(
            "modules.sse.views.parse_sse_request",
            side_effect=ValueError("Invalid data"),
        ) as mock_parse:

            url = reverse("sse-subscribe")
            response = api_client_auth.put(url, invalid_data, format="json")

            mock_parse.assert_called_once_with(invalid_data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.data == {"error": "Invalid data"}


class TestSSEUnsubscribeView:
    def test_unsubscribe_put_success(
        self,
        api_client_auth,
        valid_request_data,
        mock_parsed_params,
        mock_connection_id,
        mock_symbols,
    ):
        with (
            patch(
                "modules.sse.views.parse_sse_request",
                return_value=mock_parsed_params,
            ) as mock_parse,
            patch("modules.sse.views.unsubscribe") as mock_unsubscribe,
            patch("modules.sse.views.logging.debug") as mock_logging_debug,
        ):

            url = reverse("sse-unsubscribe")
            response = api_client_auth.put(url, valid_request_data, format="json")

            mock_parse.assert_called_once_with(valid_request_data)
            mock_unsubscribe.assert_called_once_with(mock_connection_id, mock_symbols)
            mock_logging_debug.assert_called_once_with(
                f"{mock_connection_id}: Unsubscribed from symbols: {mock_symbols}"
            )
            assert response.status_code == status.HTTP_200_OK
            assert isinstance(response, HttpResponse)
            assert (
                response.content.decode() == f"Unsubscribed from events: {mock_symbols}"
            )

    def test_unsubscribe_put_invalid_data(self, api_client_auth):
        invalid_data = {}  # Empty data

        with patch(
            "modules.sse.views.parse_sse_request",
            side_effect=ValueError("Invalid data"),
        ) as mock_parse:
            url = reverse("sse-unsubscribe")
            response = api_client_auth.put(url, invalid_data, format="json")

            mock_parse.assert_called_once_with(invalid_data)
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert response.data == {"error": "Invalid data"}
