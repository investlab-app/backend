import uuid
from dataclasses import asdict, dataclass
from json import dumps, loads

import faker
import pytest
from django.urls import reverse
from pydantic import BaseModel

from modules.core.tests.conftest import api_client, api_client_auth, user
from modules.graph_lang.models import (
    BuySellEffect,
    Graph,
    GraphEffect,
    NotificationEffect,
)
from modules.graph_lang.tests.conftest import fake_graph
from modules.graph_lang.tests.conftest_mocks import (
    MockParser,
    MockValidator,
    MockValidatorError,
)
from modules.instruments.tests.conftest import create_fake_instrument
from modules.investors.tests.conftest import create_fake_investor

fake = faker.Faker()


pytestmark = pytest.mark.django_db


class MockParserReturn(BaseModel):
    some_data: str


class TestGraphListCreate:
    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch, user):
        self.url = reverse("graph-list-create")
        self.investor = create_fake_investor(clerk_id=user.id, save=True)
        self.other_investor = create_fake_investor(clerk_id="im_a_fake", save=True)
        self.parser = MockParser()
        self.validator = MockValidator()

        monkeypatch.setattr(
            "modules.graph_lang.serializers.Parser", lambda: self.parser
        )
        monkeypatch.setattr(
            "modules.graph_lang.serializers.Validator", lambda: self.validator
        )

    def test_create__parser_fail(self, api_client_auth):
        self.parser.set_data(None)

        response = api_client_auth.post(
            self.url, {"name": "name", "raw_graph_data": "hehexd"}, format="json"
        )
        errors = response.data["non_field_errors"]

        assert response.status_code == 400
        assert len(errors) == 1
        assert errors[0].code == "parse_error"

    def test_create__validator_fail(self, api_client_auth):
        graph_data = dumps({"graph_data": "fdasf"})
        parser_return = {"ooh a graph": "hehexd"}
        self.parser.set_data(parser_return)
        self.validator.set_errors(
            [MockValidatorError(id="1"), MockValidatorError(id="2")]
        )

        response = api_client_auth.post(
            self.url, {"name": "name", "raw_graph_data": graph_data}, format="json"
        )
        errors = response.data["non_field_errors"]

        assert response.status_code == 400
        assert loads(errors[0]) == {"id": "1", "msg": "error"}
        assert loads(errors[1]) == {"id": "2", "msg": "error"}
        assert self.parser.called_with == graph_data
        assert self.validator.called_with == parser_return

    def test_create__success(self, api_client_auth):
        graph_data = {"graph_data": "fdasf"}
        parser_return = MockParserReturn(some_data="hehexd")
        self.parser.set_data(parser_return)
        self.validator.set_errors([])

        response = api_client_auth.post(
            self.url,
            {
                "name": "name",
                "raw_graph_data": graph_data,
                "active": True,
                "repeat": False,
            },
            format="json",
        )

        assert response.status_code == 201
        assert len(Graph.objects.all()) == 1

        graph = Graph.objects.first()
        assert graph.raw_graph_data == graph_data
        assert MockParserReturn.model_validate(graph.graph_data) == parser_return
        assert graph.investor == self.investor
        assert graph.name == "name"
        assert graph.active is True
        assert graph.repeat is False

    def test_get__success(self, api_client_auth):
        graph = fake_graph(investor=self.investor, save=True)

        url = reverse("graph-detail", args=[graph.id])
        response = api_client_auth.get(url)

        result = response.data
        assert response.status_code == 200
        assert result["raw_graph_data"] == graph.raw_graph_data
        assert result["id"] == str(graph.id)

    def test_get__invalid_investor__returns_404(self, api_client_auth):
        graph = fake_graph(investor=self.other_investor, save=True)

        url = reverse("graph-detail", args=[graph.id])
        response = api_client_auth.get(url)

        assert response.status_code == 404

    def test_list_single__returns_valid_graph(self, api_client_auth):
        graph = fake_graph(investor=self.investor, save=True)

        response = api_client_auth.get(self.url)

        result = response.data["results"][0]
        assert result["raw_graph_data"] == graph.raw_graph_data
        assert result["id"] == str(graph.id)

    def test_list__ignores_other_investors(self, api_client_auth):
        [fake_graph(investor=self.investor, save=True) for _ in range(3)]
        [fake_graph(investor=self.other_investor, save=True) for _ in range(2)]

        response = api_client_auth.get(self.url)
        assert response.status_code == 200
        assert response.data["count"] == 3

    def test_update__success(self, api_client_auth):
        graph = fake_graph(investor=self.investor, save=True)
        new_raw = {"updated": "data"}
        parser_return = MockParserReturn(some_data="aaa")

        self.parser.set_data(parser_return)
        self.validator.set_errors([])

        url = reverse("graph-detail", args=[graph.id])
        response = api_client_auth.patch(
            url, {"raw_graph_data": new_raw}, format="json"
        )

        graph.refresh_from_db()
        assert response.status_code == 200
        assert graph.raw_graph_data == new_raw
        assert graph.graph_data == parser_return.model_dump()

    def test_update__parser_fail(self, api_client_auth):
        graph = fake_graph(investor=self.investor, save=True)
        url = reverse("graph-detail", args=[graph.id])
        self.parser.set_data(None)

        response = api_client_auth.patch(
            url, {"raw_graph_data": "invalid"}, format="json"
        )
        errors = response.data["non_field_errors"]

        assert response.status_code == 400
        assert errors[0].code == "parse_error"

    def test_update__validator_fail(self, api_client_auth):
        graph = fake_graph(investor=self.investor, save=True)
        url = reverse("graph-detail", args=[graph.id])
        new_raw = dumps({"updated": "data"})
        parser_return = {"parsed": "data"}
        self.parser.set_data(parser_return)
        self.validator.set_errors([MockValidatorError(id="10")])

        response = api_client_auth.patch(
            url, {"raw_graph_data": new_raw}, format="json"
        )
        errors = response.data["non_field_errors"]

        assert response.status_code == 400
        assert loads(errors[0]) == {"id": "10", "msg": "error"}

    def test_update__forbidden_for_other_investor(self, api_client_auth):
        graph = fake_graph(investor=self.other_investor, save=True)
        url = reverse("graph-detail", args=[graph.id])
        response = api_client_auth.patch(
            url, {"raw_graph_data": dumps({"x": 1})}, format="json"
        )
        assert response.status_code == 404

    def test_delete__success(self, api_client_auth):
        graph = fake_graph(investor=self.investor, save=True)
        url = reverse("graph-detail", args=[graph.id])

        response = api_client_auth.delete(url)

        assert response.status_code == 204
        assert not Graph.objects.filter(id=graph.id).exists()

    def test_delete__forbidden_for_other_investor(self, api_client_auth):
        graph = fake_graph(investor=self.other_investor, save=True)
        url = reverse("graph-detail", args=[graph.id])

        response = api_client_auth.delete(url)

        assert response.status_code == 404
        assert Graph.objects.filter(id=graph.id).exists()


class TestGraphResultView:
    @pytest.fixture(autouse=True)
    def setup(self, user):
        self.investor = create_fake_investor(clerk_id=user.id, save=True)
        self.other_investor = create_fake_investor(clerk_id="ima fake", save=True)
        self.graph = fake_graph(investor=self.investor, save=True)

    def url(self, id_=None):
        id_ = id_ or self.graph.id
        return reverse("graph-result", args=[id_])

    def test_unauthorized(self, api_client):
        response = api_client.get(self.url())

        assert response.status_code == 403

    def test_wrong_user(self, api_client_auth):
        graph = fake_graph(investor=self.other_investor, save=True)
        url = self.url(graph.id)

        response = api_client_auth.get(url)

        assert response.status_code == 404

    def test_no_such_graph(self, api_client_auth):
        url = self.url(uuid.uuid4())

        response = api_client_auth.get(url)

        assert response.status_code == 404

    def test_no_effects__get_produces_empty_list(self, api_client_auth):
        url = self.url()
        response = api_client_auth.get(url)

        assert response.json()["results"] == []

    def create_transaction_effect(
        self, graph, success, instrument, is_buy, amount, action_price
    ):
        transaction_effect = BuySellEffect.objects.create(
            instrument=instrument,
            is_buy=is_buy,
            amount=amount,
            action_price=action_price,
        )
        GraphEffect.objects.create(
            graph=graph, success=success, effect=transaction_effect
        )

    def create_notification_effect(self, graph, success, format_, message):
        transaction_effect = NotificationEffect.objects.create(
            format=format_, message=message
        )
        GraphEffect.objects.create(
            graph=graph, success=success, effect=transaction_effect
        )

    def test_single_buy_effect(self, api_client_auth):
        instrument = create_fake_instrument(ticker="AAPL", save=True)
        self.create_transaction_effect(
            graph=self.graph,
            success=True,
            instrument=instrument,
            is_buy=True,
            amount=40,
            action_price=10,
        )

        response = api_client_auth.get(self.url()).json()

        result = response["results"][0]
        assert len(response["results"]) == 1
        assert result["effect"] == {
            "instrument": {"ticker": "AAPL"},
            "is_buy": True,
            "amount": 40.0,
            "effect_type": "transaction",
            "action_price": 10.0,
        }
        assert result["success"] is True

    def test_single_notification_effect(self, api_client_auth):
        self.create_notification_effect(
            graph=self.graph,
            success=True,
            format_=NotificationEffect.PUSH,
            message="hehexd",
        )

        response = api_client_auth.get(self.url()).json()

        result = response["results"][0]
        assert len(response["results"]) == 1
        assert result["effect"] == {
            "format": "push",
            "message": "hehexd",
            "effect_type": "notification",
        }
        assert result["success"] is True

    def test_multiple_effects__response_length_is_correct(self, api_client_auth):
        instrument = create_fake_instrument(ticker="AAPL", save=True)
        self.create_notification_effect(
            graph=self.graph,
            success=True,
            format_=NotificationEffect.PUSH,
            message="hehexd",
        )
        self.create_transaction_effect(
            graph=self.graph,
            success=True,
            instrument=instrument,
            is_buy=True,
            action_price=50,
            amount=40,
        )

        response = api_client_auth.get(self.url()).json()

        assert len(response["results"]) == 2


# TODO Move create_*_effect to conftest
