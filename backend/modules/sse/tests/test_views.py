from unittest.mock import patch

import pytest
from django.http import HttpResponse
from django.urls import reverse
from rest_framework import status

from modules.core.tests.conftest import api_client_auth
from modules.users.tests.conftest import user

pytestmark = pytest.mark.django_db


class TestSSESubscribeView:
    def test_subscribe_put_success(
        self,
        api_client_auth,
        valid_request_data,
        mock_parsed_params,
        mock_connection_id,
        mock_symbols,
    ):
        """
        Tests that a successful PUT request to the SSE subscribe endpoint results in correct parsing, subscription, logging, and a 200 OK response with a confirmation message.
        """
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
        """
        Tests that a PUT request with invalid subscription data returns a 400 error response.
        
        Simulates a failure in parsing the request data by raising a ValueError, and verifies that the view responds with an appropriate error message and HTTP 400 status.
        """
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
        """
        Tests that a successful PUT request to the unsubscribe endpoint unsubscribes the client from specified symbols.
        
        Verifies that the request data is parsed, the unsubscribe function is called with the correct parameters, a debug log entry is made, and the response confirms successful unsubscription.
        """
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
        """
        Tests that a PUT request with invalid data to the SSE unsubscribe endpoint returns a 400 error.
        
        Verifies that when the request data is invalid and parsing fails, the view responds with an appropriate error message and status code.
        """
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
