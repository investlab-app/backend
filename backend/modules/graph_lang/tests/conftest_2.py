from typing import Any, Optional
from dataclasses import dataclass, field

from modules.graph_lang.framework.parser import GraphData, NodeData, EdgeData


class MockParser:

    def parse(self, json :dict) -> Optional[Any]:
        self.called_with = json
        return self.data

    def set_data(self, data :Any):
        self.data = data

    def get_call_args(self):
        return self.called_with

class MockValidator:
    def __init__(self):
        self.errors = [] 

    def validate(self, data):
        self.called_with = data
        return self.errors

    def set_errors(self, errors :list):
        self.errors = errors

    def get_call_args(self):
        return self.called_with

@dataclass
class MockValidatorError:
    id :str
    msg :str= field(default='error', init=False)

empty_graph_data = GraphData()