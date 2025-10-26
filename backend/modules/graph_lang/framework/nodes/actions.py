from modules.graph_lang.framework import edges
from modules.graph_lang.framework.nodes.node import Node
from modules.graph_lang.framework.actions import GraphActionSet, BuySellAction

class BuySellAmountNode(Node):
    action = edges.EnumType(direction=edges.INPUT, allowed_values=['buy', 'sell'])
    amount = edges.NumberType(direction=edges.INPUT)
    ticker = edges.InstrumentType(direction=edges.INPUT)

    out = edges.VoidType(direction=edges.OUTPUT)

    action_set :GraphActionSet

    def __init__(self, action_set :GraphActionSet):
        super().__init__()
        self.action_set = action_set

    def execute(self):
        action = BuySellAction(
            action = self.action(),
            amount = self.amount(),
            ticker = self.ticker()
        )
        self.action_set.add_action(action)

        self.out.set(None)