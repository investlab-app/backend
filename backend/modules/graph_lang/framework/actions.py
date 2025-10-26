from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

class GraphActionSet:
    _actions :set = set()
    
    def add_action(self, action):
        self._actions.add(action)

    def get_actions(self):
        return self._actions


@dataclass(frozen=True)
class BuySellAction:
    action :Literal['buy', 'sell']
    amount :Decimal
    ticker :str
