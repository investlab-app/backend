import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_status(api_client):
    url = reverse("status")
    response = api_client.get(url)
    assert response.status_code == 200
    assert response.json() == {"message": "App is running!"}
