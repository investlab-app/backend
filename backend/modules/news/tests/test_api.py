import pytest
from django.urls import reverse

from modules.core.tests.conftest import api_client, api_client_auth  # noqa: F401

pytestmark = pytest.mark.django_db


class TestNewsListEndpoint:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.url = reverse("news-list")

    def test_happy(self, api_client_auth, mocker, fake_news):
        mocker.patch(
            "modules.news.repositories.PolygonNewsRepository.list_news",
            return_value=iter(fake_news),
        )
        response = api_client_auth.get(self.url)
        assert response.status_code == 200
        assert len(response.data) == 5
        assert response.data[0]["title"] == "Test news 0"

    def test_no_auth(self, api_client):
        response = api_client.get(self.url)
        assert response.status_code == 403

    def test_number_of_news_param(self, api_client_auth, mocker, fake_news):
        mocker.patch(
            "modules.news.repositories.PolygonNewsRepository.list_news",
            return_value=iter(fake_news),
        )
        response = api_client_auth.get(self.url, {"number_of_news": 3})
        assert response.status_code == 200
        assert len(response.data) == 3
