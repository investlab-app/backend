from modules.core.constants import PrecisionType
from modules.orders.order_engine.engine import TradeEngine
from modules.orders.order_engine.structures import EngineTransaction, TradeEngineInput


def _order_ids_match(orders, ids):
    return {o.id for o in orders} == set(ids)


def _transactions_match(done_transactions, expected_transactions):
    for tx1, tx2 in zip(done_transactions, expected_transactions, strict=False):
        if tx1.ticker != tx2.ticker:
            return False
        if tx1.is_buy != tx2.is_buy:
            return False
        if tx1.investor_id != tx2.investor_id:
            return False
        if abs(tx1.volume - tx2.volume) > PrecisionType.volume.precision:
            return False
    return True


def _run_test(
    engine_input: TradeEngineInput,
    transactions: list[EngineTransaction],
    modified_orders: list[str],
    completed_orders: list[str],
):
    engine = TradeEngine()
    result = engine.run(engine_input)

    assert _transactions_match(result.transactions, transactions)
    assert _order_ids_match(result.updated_orders, modified_orders)
    assert (set(result.completed_orders)) == set(completed_orders)
