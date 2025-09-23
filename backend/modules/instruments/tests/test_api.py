import pytest
from django.urls import reverse

from modules.core.tests.conftest import api_client, api_client_auth

pytestmark = pytest.mark.django_db


class TestInstrumentListEndpoint:
    @pytest.fixture(autouse=True)
    def setup(self, instruments_factory):
        self.instruments = [instruments_factory() for _ in range(3)]
        self.url = reverse("instruments-list")

    def test_happy(self, api_client_auth, instruments_factory):
        response = api_client_auth.get(self.url)
        assert response.status_code == 200
        assert len(response.data["results"]) == len(self.instruments)

    def test_no_auth(self, api_client, instruments_factory):
        response = api_client.get(self.url)
        assert response.status_code == 403


class TestInstrumentDetailEndpoint:
    @pytest.fixture(autouse=True)
    def setup(self, instruments_factory):
        self.instruments = [instruments_factory() for _ in range(3)]

    def test_happy(self, api_client_auth):
        instrument = self.instruments[0]
        url = reverse("instrument-detail", query={"ticker": instrument.ticker})
        response = api_client_auth.get(url)
        assert response.status_code == 200
        assert response.data["id"] == str(instrument.id)
        assert response.data["ticker"] == instrument.ticker
        assert response.data["name"] == instrument.name

    def test_not_found(self, api_client_auth):
        url = reverse("instrument-detail", query={"ticker": "999"})
        response = api_client_auth.get(url)
        assert response.status_code == 404

    def test_no_auth(self, api_client):
        instrument = self.instruments[0]
        url = reverse("instrument-detail", query={"ticker": instrument.ticker})
        response = api_client.get(url)
        assert response.status_code == 403

    def test_incorrect_query_params(self, api_client_auth):
        instrument = self.instruments[0]
        url = reverse(
            "instrument-detail", query={"ticker": instrument.ticker, "cik": "123"}
        )
        response = api_client_auth.get(url)
        assert response.status_code == 400

    def test_missing_query_params(self, api_client_auth):
        url = reverse("instrument-detail")
        response = api_client_auth.get(url)
        assert response.status_code == 400
