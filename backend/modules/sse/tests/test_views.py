from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response

from config import container
from modules.core.tests.conftest import api_client_auth
from modules.users.tests.conftest import user

pytestmark = pytest.mark.django_db


# class TestSSESubscribeView:
#     def test_subscribe_put_success(
#         self,
#         api_client_auth,
#         valid_request_data,
#         mock_parsed_params,
#         mock_symbols,
#     ):
#         with (
#             patch(
#                 "modules.sse.schemas.SSERequestParams.parse",
#                 return_value=mock_parsed_params,
#             ) as mock_parse,
#         ):
#             url = reverse("sse-subscribe")
#             response = api_client_auth.put(url, valid_request_data, format="json")

#             mock_parse.assert_called_once_with(valid_request_data)
#             assert response.status_code == status.HTTP_200_OK
#             assert isinstance(response, Response)
#             assert response.data == {
#                 "message": f"Subscribed to new events: {mock_symbols}"
#             }

#     def test_subscribe_put_invalid_data(self, api_client_auth):
#         invalid_data = {"symbols": "AAPL"}  # Missing connectionId

#         with patch(
#             "modules.sse.schemas.SSERequestParams.parse",
#             side_effect=ValueError("Invalid data"),
#         ) as mock_parse:
#             url = reverse("sse-subscribe")
#             response = api_client_auth.put(url, invalid_data, format="json")

#             mock_parse.assert_called_once_with(invalid_data)
#             assert response.status_code == status.HTTP_400_BAD_REQUEST
#             assert response.data == {"error": "Invalid data"}


# class TestSSEUnsubscribeView:
#     def test_unsubscribe_put_success(
#         self,
#         api_client_auth,
#         valid_request_data,
#         mock_parsed_params,
#         mock_connection_id,
#         mock_symbols,
#     ):
#         with (
#             patch(
#                 "modules.sse.schemas.SSERequestParams.parse",
#                 return_value=mock_parsed_params,
#             ) as mock_parse,
#         ):
#             url = reverse("sse-unsubscribe")
#             response = api_client_auth.put(url, valid_request_data, format="json")

#             mock_parse.assert_called_once_with(valid_request_data)
#             assert response.status_code == status.HTTP_200_OK
#             assert isinstance(response, Response)
#             assert response.data == {
#                 "message": f"Unsubscribed from events: {mock_symbols}"
#             }

#     def test_unsubscribe_put_invalid_data(self, api_client_auth):
#         invalid_data = {}  # Empty data

#         with patch(
#             "modules.sse.schemas.SSERequestParams.parse",
#             side_effect=ValueError("Invalid data"),
#         ) as mock_parse:
#             url = reverse("sse-unsubscribe")
#             response = api_client_auth.put(url, invalid_data, format="json")

#             mock_parse.assert_called_once_with(invalid_data)
#             assert response.status_code == status.HTTP_400_BAD_REQUEST
#             assert response.data == {"error": "Invalid data"}
