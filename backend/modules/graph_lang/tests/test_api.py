import pytest
from pydantic import BaseModel
from dataclasses import dataclass, asdict
from django.urls import reverse
from json import dumps, loads
from modules.core.tests.conftest import api_client_auth, api_client, user
from modules.investors.tests.conftest import create_fake_investor
from modules.graph_lang.tests.conftest_mocks import (
    MockParser,
    MockValidator,
    MockValidatorError,
)
from modules.graph_lang.models import Graph
import faker

fake = faker.Faker()


def fake_graph(investor, *, save=False) -> Graph:
    graph = Graph(
        investor=investor,
        raw_graph_data=dumps({fake.pystr(): fake.pystr()}),
        graph_data=dumps({fake.pystr(): fake.pystr()}),
    )
    if save:
        graph.save()
    return graph


pytestmark = pytest.mark.django_db

class MockParserReturn(BaseModel):
    some_data :str

class TestGraphListCreate:

    @pytest.fixture(autouse=True)
    def setup(self, monkeypatch, user):
        self.url = reverse('graph-list-create')
        self.investor = create_fake_investor(clerk_id=user.id, save=True)
        self.other_investor = create_fake_investor(clerk_id='im_a_fake', save=True)
        self.parser = MockParser()
        self.validator = MockValidator()

        monkeypatch.setattr('modules.graph_lang.serializers.Parser', lambda: self.parser)
        monkeypatch.setattr('modules.graph_lang.serializers.Validator', lambda: self.validator)


    def test_create__parser_fail(self, api_client_auth):
        self.parser.set_data(None)

        response = api_client_auth.post(self.url, {'name': 'name', 'raw_graph_data': 'hehexd'}, format='json')
        errors = response.data['non_field_errors']

        assert response.status_code == 400
        assert len(errors) == 1
        assert errors[0].code == 'parse_error'

    def test_create__validator_fail(self, api_client_auth):
        graph_data = dumps({'graph_data': 'fdasf'})
        parser_return = {'ooh a graph': 'hehexd'}
        self.parser.set_data(parser_return)
        self.validator.set_errors([
            MockValidatorError(id='1'),
            MockValidatorError(id='2')
        ])

        response = api_client_auth.post(self.url, {'name': 'name', 'raw_graph_data': graph_data}, format='json')
        errors = response.data['non_field_errors']

        assert response.status_code == 400
        assert loads(errors[0]) == {'id': '1', 'msg': 'error'}
        assert loads(errors[1]) == {'id': '2', 'msg': 'error'}
        assert self.parser.called_with == graph_data
        assert self.validator.called_with == parser_return

    def test_create__success(self, api_client_auth):
        graph_data = dumps({'graph_data': 'fdasf'})
        parser_return = MockParserReturn(some_data='hehexd')
        self.parser.set_data(parser_return)
        self.validator.set_errors([])

        response = api_client_auth.post(self.url, {'raw_graph_data': graph_data}, format='json')

        assert response.status_code == 201
        assert len(Graph.objects.all()) == 1

        graph = Graph.objects.first()
        assert loads(graph.raw_graph_data) == loads(graph_data)
        assert MockParserReturn.model_validate(loads(graph.graph_data)) == parser_return
        assert graph.investor == self.investor

    def test_get__returns_valid_graph(self, api_client_auth):
        graph = fake_graph(self.investor, save=True)

        url = reverse('graph-detail', args=[graph.id])
        response = api_client_auth.get(url)

        result = response.data
        assert response.status_code == 200
        assert result['raw_graph_data'] == graph.raw_graph_data
        assert result['graph_data'] == graph.graph_data

    def test_get__invalid_investor__returns_404(self, api_client_auth):
        graph = fake_graph(self.other_investor, save=True)

        url = reverse('graph-detail', args=[graph.id])
        response = api_client_auth.get(url)

        assert response.status_code == 404

    def test_list_single__returns_valid_graph(self, api_client_auth):
        graph = fake_graph(self.investor, save=True)

        response = api_client_auth.get(self.url)

        result = response.data['results'][0]
        assert result['raw_graph_data'] == graph.raw_graph_data
        assert result['graph_data'] == graph.graph_data


    def test_list__ignores_other_investors(self, api_client_auth):
        [fake_graph(self.investor, save=True) for _ in range(3)]
        [fake_graph(self.other_investor, save=True) for _ in range(2)]

        response = api_client_auth.get(self.url)
        assert response.status_code == 200
        assert response.data['count'] == 3


    def test_update__success(self, api_client_auth):
        graph = fake_graph(self.investor, save=True)
        new_raw = dumps({'updated': 'data'})
        parser_return = {'parsed': 'data'}

        self.parser.set_data(parser_return)
        self.validator.set_errors([])

        url = reverse('graph-detail', args=[graph.id])
        response = api_client_auth.patch(url, {'raw_graph_data': new_raw}, format='json')

        graph.refresh_from_db()
        assert response.status_code == 200
        assert loads(graph.raw_graph_data) == loads(new_raw)
        assert loads(graph.graph_data) == parser_return

    def test_update__parser_fail(self, api_client_auth):
        graph = fake_graph(self.investor, save=True)
        url = reverse('graph-detail', args=[graph.id])
        self.parser.set_data(None)

        response = api_client_auth.patch(url, {'raw_graph_data': 'invalid'}, format='json')
        errors = response.data['non_field_errors']

        assert response.status_code == 400
        assert errors[0].code == 'parse_error'

    def test_update__validator_fail(self, api_client_auth):
        graph = fake_graph(self.investor, save=True)
        url = reverse('graph-detail', args=[graph.id])
        new_raw = dumps({'updated': 'data'})
        parser_return = {'parsed': 'data'}
        self.parser.set_data(parser_return)
        self.validator.set_errors([MockValidatorError(id='10')])

        response = api_client_auth.patch(url, {'raw_graph_data': new_raw}, format='json')
        errors = response.data['non_field_errors']

        assert response.status_code == 400
        assert loads(errors[0]) == {'id': '10', 'msg': 'error'}

    def test_update__forbidden_for_other_investor(self, api_client_auth):
        graph = fake_graph(self.other_investor, save=True)
        url = reverse('graph-detail', args=[graph.id])
        response = api_client_auth.patch(url, {'raw_graph_data': dumps({'x': 1})}, format='json')
        assert response.status_code == 404

    def test_delete__success(self, api_client_auth):
        graph = fake_graph(self.investor, save=True)
        url = reverse('graph-detail', args=[graph.id])

        response = api_client_auth.delete(url)

        assert response.status_code == 204
        assert not Graph.objects.filter(id=graph.id).exists()

    def test_delete__forbidden_for_other_investor(self, api_client_auth):
        graph = fake_graph(self.other_investor, save=True)
        url = reverse('graph-detail', args=[graph.id])

        response = api_client_auth.delete(url)

        assert response.status_code == 404
        assert Graph.objects.filter(id=graph.id).exists()
