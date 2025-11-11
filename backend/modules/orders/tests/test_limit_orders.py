from decimal import Decimal

import pytest

from modules.orders.order_engine.structures import (
    EngineAsset,
    EngineTransaction,
    LimitEngineOrder,
    TradeEngineInput,
)
from modules.orders.tests.utils import _run_test

TEST_INVESTOR_ID = "816e3548-a012-412d-879a-cc742b58e721"


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
            assets=[
                EngineAsset(
                    investor_id=TEST_INVESTOR_ID, ticker="AAPL", volume=Decimal(1)
                )
            ],
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
            assets=[
                EngineAsset(
                    investor_id=TEST_INVESTOR_ID, ticker="AAPL", volume=Decimal(1)
                )
            ],
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
            assets=[
                EngineAsset(
                    investor_id=TEST_INVESTOR_ID, ticker="AAPL", volume=Decimal(5)
                )
            ],
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
