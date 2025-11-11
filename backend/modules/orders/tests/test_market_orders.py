from decimal import Decimal

import pytest

from modules.orders.order_engine.structures import (
    EngineAsset,
    EngineTransaction,
    MarketEngineOrder,
    TradeEngineInput,
)
from modules.orders.tests.conftest import uuids
from modules.orders.tests.utils import _run_test

TEST_INVESTOR_ID = "816e3548-a012-412d-879a-cc742b58e721"


def test_no_orders():
    _run_test(
        engine_input=TradeEngineInput(orders=[], assets=[], prices={}, balances={}),
        transactions=[],
        modified_orders=[],
        completed_orders=[],
    )


def test_market_buy_order__no_money__no_transaction(uuids):
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=True,
                )
            ],
            assets=[],
            prices={"AAPL": Decimal(10)},
            balances={TEST_INVESTOR_ID: Decimal(0)},
        ),
        transactions=[],
        modified_orders=[],
        completed_orders=[],
    )


def test_market_buy_order__not_enough_money__buys_partial(uuids):
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=True,
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


def test_market_buy_order__success(uuids):
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=True,
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


def test_market_buy_order__decimal_values__success(uuids):
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(0.00003),
                    is_buy=True,
                )
            ],
            assets=[],
            prices={"AAPL": Decimal(1000.501)},
            balances={TEST_INVESTOR_ID: Decimal(45.82)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL",
                volume=Decimal(0.00003),
                is_buy=True,
                investor_id=TEST_INVESTOR_ID,
            )
        ],
        modified_orders=[],
        completed_orders=[uuids[0]],
    )


def test_market_buy_order__decimal_values__buys_partial(uuids):
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(0.003),
                    is_buy=True,
                )
            ],
            assets=[],
            prices={"AAPL": Decimal(1000)},
            balances={TEST_INVESTOR_ID: Decimal(1.82)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL",
                volume=Decimal(0.00182),
                is_buy=True,
                investor_id=TEST_INVESTOR_ID,
            )
        ],
        modified_orders=[uuids[0]],
        completed_orders=[],
    )


def test_market_two_buy_orders__not_enough_balance__one_partial(uuids):
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(1.5),
                    is_buy=True,
                ),
                MarketEngineOrder(
                    id=uuids[1],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(3.5),
                    is_buy=True,
                ),
            ],
            assets=[
                EngineAsset(
                    investor_id=TEST_INVESTOR_ID, ticker="AAPL", volume=Decimal(2)
                )
            ],
            prices={"AAPL": Decimal(50)},
            balances={TEST_INVESTOR_ID: Decimal(100)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL",
                volume=Decimal(1.5),
                is_buy=True,
                investor_id=TEST_INVESTOR_ID,
            ),
            EngineTransaction(
                ticker="AAPL",
                volume=Decimal(0.5),
                is_buy=True,
                investor_id=TEST_INVESTOR_ID,
            ),
        ],
        modified_orders=[uuids[1]],
        completed_orders=[uuids[0]],
    )


def test_market_sell_order__success(uuids):
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=False,
                )
            ],
            assets=[
                EngineAsset(
                    investor_id=TEST_INVESTOR_ID, ticker="AAPL", volume=Decimal(1)
                )
            ],
            prices={"AAPL": Decimal(10)},
            balances={TEST_INVESTOR_ID: Decimal(25)},
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


def test_market_sell_order__decimal_values__success(uuids):
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(0.3009),
                    is_buy=False,
                )
            ],
            assets=[
                EngineAsset(
                    investor_id=TEST_INVESTOR_ID, ticker="AAPL", volume=Decimal(0.54)
                )
            ],
            prices={"AAPL": Decimal(100.5)},
            balances={TEST_INVESTOR_ID: Decimal(45.8)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL",
                volume=Decimal(0.3009),
                is_buy=False,
                investor_id=TEST_INVESTOR_ID,
            )
        ],
        modified_orders=[],
        completed_orders=[uuids[0]],
    )


def test_market_sell_order__decimal_values__sells_partial(uuids):
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(0.3009),
                    is_buy=False,
                )
            ],
            assets=[
                EngineAsset(
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(0.240001),
                )
            ],
            prices={"AAPL": Decimal(100.5)},
            balances={TEST_INVESTOR_ID: Decimal(45.8)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL",
                volume=Decimal(0.240001),
                is_buy=False,
                investor_id=TEST_INVESTOR_ID,
            )
        ],
        modified_orders=[uuids[0]],
        completed_orders=[],
    )


def test_order__price_not_given__ignores_order(uuids):
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=False,
                ),
                MarketEngineOrder(
                    id=uuids[1],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="MSFT",
                    volume=Decimal(1),
                    is_buy=False,
                ),
            ],
            assets=[
                EngineAsset(
                    investor_id=TEST_INVESTOR_ID, ticker="AAPL", volume=Decimal(1)
                ),
                EngineAsset(
                    investor_id=TEST_INVESTOR_ID, ticker="MSFT", volume=Decimal(1)
                ),
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


def test_market_sell_order__not_enough_assets__sells_partial(uuids):
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(10),
                    is_buy=False,
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


def test_market_two_sell_orders__enough_assets_owned__sells_all(uuids):
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=False,
                ),
                MarketEngineOrder(
                    id=uuids[1],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(3),
                    is_buy=False,
                ),
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
                volume=Decimal(1),
                is_buy=False,
                investor_id=TEST_INVESTOR_ID,
            ),
            EngineTransaction(
                ticker="AAPL",
                volume=Decimal(3),
                is_buy=False,
                investor_id=TEST_INVESTOR_ID,
            ),
        ],
        modified_orders=[],
        completed_orders=[uuids[0], uuids[1]],
    )


def test_market_two_sell_orders__not_enough_assets_owned__one_partial(uuids):
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id=uuids[0],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=False,
                ),
                MarketEngineOrder(
                    id=uuids[1],
                    investor_id=TEST_INVESTOR_ID,
                    ticker="AAPL",
                    volume=Decimal(3),
                    is_buy=False,
                ),
            ],
            assets=[
                EngineAsset(
                    investor_id=TEST_INVESTOR_ID, ticker="AAPL", volume=Decimal(2)
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
            ),
            EngineTransaction(
                ticker="AAPL",
                volume=Decimal(1),
                is_buy=False,
                investor_id=TEST_INVESTOR_ID,
            ),
        ],
        modified_orders=[uuids[1]],
        completed_orders=[uuids[0]],
    )
