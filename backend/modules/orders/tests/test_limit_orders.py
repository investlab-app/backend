import uuid
from decimal import Decimal

from modules.core.constants import PrecisionType
from modules.orders.order_engine.engine import TradeEngine
from modules.orders.order_engine.structures import (
    EngineAsset,
    EngineTransaction,
    LimitEngineOrder,
    TradeEngineInput,
)


TEST_INVESTOR_ID = "816e3548-a012-412d-879a-cc742b58e721"


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


def test_limit_buy_not_triggered(uuids):
    # Limit buy with limit_price < market price -> should not execute
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                LimitEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=True,
                    limit_price=Decimal(9),
                )
            ],
            assets=[],
            prices={"AAPL": Decimal(10)},
            balances={TEST_INVESTOR_ID: Decimal(100)},
        ),
        transactions=[],
        modified_orders=[],
        completed_orders=[],
    )


def test_limit_buy_triggered_success(uuids):
    # Limit buy where market price <= limit_price
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                LimitEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=True,
                    limit_price=Decimal(11),
                )
            ],
            assets=[],
            prices={"AAPL": Decimal(10)},
            balances={TEST_INVESTOR_ID: Decimal(15)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL",
                volume=Decimal(1),
                is_buy=True,
                investor_id=TEST_INVESTOR_ID,
            )
        ],
        modified_orders=[],
        completed_orders=[uuids[0]],
    )


def test_limit_buy_partial_due_to_balance(uuids):
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                LimitEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=True,
                    limit_price=Decimal(10),
                )
            ],
            assets=[],
            prices={"AAPL": Decimal(10)},
            balances={TEST_INVESTOR_ID: Decimal(5)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL",
                volume=Decimal(0.5),
                is_buy=True,
                investor_id=TEST_INVESTOR_ID,
            )
        ],
        modified_orders=[uuids[0]],
        completed_orders=[],
    )


def test_limit_sell_not_triggered(uuids):
    # Limit sell where market price < limit_price -> should not execute
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                LimitEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=False,
                    limit_price=Decimal(11),
                )
            ],
            assets=[EngineAsset(investor_id=TEST_INVESTOR_ID, ticker="AAPL", volume=Decimal(1))],
            prices={"AAPL": Decimal(10)},
            balances={TEST_INVESTOR_ID: Decimal(100)},
        ),
        transactions=[],
        modified_orders=[],
        completed_orders=[],
    )


def test_limit_sell_triggered_success(uuids):
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                LimitEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=False,
                    limit_price=Decimal(9),
                )
            ],
            assets=[EngineAsset(investor_id=TEST_INVESTOR_ID, ticker="AAPL", volume=Decimal(1))],
            prices={"AAPL": Decimal(10)},
            balances={TEST_INVESTOR_ID: Decimal(100)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL",
                volume=Decimal(1),
                is_buy=False,
                investor_id=TEST_INVESTOR_ID,
            )
        ],
        modified_orders=[],
        completed_orders=[uuids[0]],
    )


def test_limit_sell_partial_due_to_assets(uuids):
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                LimitEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(10),
                    is_buy=False,
                    limit_price=Decimal(9),
                )
            ],
            assets=[EngineAsset(investor_id=TEST_INVESTOR_ID, ticker="AAPL", volume=Decimal(5))],
            prices={"AAPL": Decimal(10)},
            balances={TEST_INVESTOR_ID: Decimal(100)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL",
                volume=Decimal(5),
                is_buy=False,
                investor_id=TEST_INVESTOR_ID,
            )
        ],
        modified_orders=[uuids[0]],
        completed_orders=[],
    )
