import pytest
from django.urls import reverse


def test_healthcheck(api_client):
    url = reverse("healthcheck")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json() == {"message": "App is running!"}
