import pytest
from modules.graph_lang.framework.nodes.node import NodeFactory, Node


class MockNodeA(Node):
    TYPE_NAME = "mockA"


class MockNodeB(Node):
    TYPE_NAME = "mockB"

    def __init__(self, *args, **kwargs):
        self.init_args = args
        self.init_kwargs = kwargs


class Mock:
    pass


class TestFactory:
    @pytest.fixture(autouse=True)
    def setup(self):
        self._mock_price_provider = Mock()
        self._mock_action_set = Mock()
        self.factory = NodeFactory()

    def test_get_type__node_does_not_exist__returns_none(self):
        assert self.factory.name_to_type("this_does_not_exist") == None

    def test_get_type__node_exists__returns_valid_type(self):
        type = self.factory.name_to_type("mockA")
        assert type == MockNodeA

    def test_get_type__type_case_mismatch__returns_valid_type(self):
        type = self.factory.name_to_type("MoCka")
        assert type == MockNodeA

    def test_from_type__invalid_type__raises_value_error(self):
        with pytest.raises(ValueError):
            self.factory.from_type(str)

    def test_from_type__valid_type__returns_valid_object(self):
        obj = self.factory.from_type(MockNodeB)

        assert type(obj) == MockNodeB
