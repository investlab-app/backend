from decimal import Decimal
from unittest.mock import Mock

from modules.core.defaults import PrecisionType
from modules.orders.order_engine.engine import TradeEngine
from modules.orders.order_engine.structures import (
    EngineAsset,
    EngineTransaction,
    MarketEngineOrder,
    TradeEngineInput,
)


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
    output_mock = Mock()
    engine = TradeEngine(
        engine_input_fetcher=Mock(side_effect=[engine_input]),
        result_handler=output_mock,
    )
    engine.run()

    result = output_mock.call_args.args[0]
    output_mock.assert_called_once()
    assert _transactions_match(result.transactions, transactions)
    assert _order_ids_match(result.updated_orders, modified_orders)
    assert _order_ids_match(result.completed_orders, completed_orders)


def test_no_orders():
    _run_test(
        engine_input=TradeEngineInput(orders=[], assets=[], prices={}, balances={}),
        transactions=[],
        modified_orders=[],
        completed_orders=[],
    )


def test_market_buy_order__no_money__no_transaction():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id="1",
                    investor_id=42,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=True,
                )
            ],
            assets=[],
            prices={"AAPL": Decimal(10)},
            balances={42: Decimal(0)},
        ),
        transactions=[],
        modified_orders=[],
        completed_orders=[],
    )


def test_market_buy_order__not_enough_money__buys_partial():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id="1",
                    investor_id=42,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=True,
                )
            ],
            assets=[],
            prices={"AAPL": Decimal(10)},
            balances={42: Decimal(5)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL", volume=Decimal(0.5), is_buy=True, investor_id=42
            )
        ],
        modified_orders=["1"],
        completed_orders=[],
    )


def test_market_buy_order__success():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id="5",
                    investor_id=42,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=True,
                )
            ],
            assets=[],
            prices={"AAPL": Decimal(10)},
            balances={42: Decimal(15)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL", volume=Decimal(1), is_buy=True, investor_id=42
            )
        ],
        modified_orders=[],
        completed_orders=["5"],
    )


def test_market_buy_order__decimal_values__success():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id="5",
                    investor_id=42,
                    ticker="AAPL",
                    volume=Decimal(0.00003),
                    is_buy=True,
                )
            ],
            assets=[],
            prices={"AAPL": Decimal(1000.501)},
            balances={42: Decimal(45.82)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL", volume=Decimal(0.00003), is_buy=True, investor_id=42
            )
        ],
        modified_orders=[],
        completed_orders=["5"],
    )


def test_market_buy_order__decimal_values__buys_partial():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id="5",
                    investor_id=42,
                    ticker="AAPL",
                    volume=Decimal(0.003),
                    is_buy=True,
                )
            ],
            assets=[],
            prices={"AAPL": Decimal(1000)},
            balances={42: Decimal(1.82)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL", volume=Decimal(0.00182), is_buy=True, investor_id=42
            )
        ],
        modified_orders=["5"],
        completed_orders=[],
    )


def test_market_two_buy_orders__not_enough_balance__one_partial():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id="1",
                    investor_id=42,
                    ticker="AAPL",
                    volume=Decimal(1.5),
                    is_buy=True,
                ),
                MarketEngineOrder(
                    id="2",
                    investor_id=42,
                    ticker="AAPL",
                    volume=Decimal(3.5),
                    is_buy=True,
                ),
            ],
            assets=[EngineAsset(investor_id=42, ticker="AAPL", volume=Decimal(2))],
            prices={"AAPL": Decimal(50)},
            balances={42: Decimal(100)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL", volume=Decimal(1.5), is_buy=True, investor_id=42
            ),
            EngineTransaction(
                ticker="AAPL", volume=Decimal(0.5), is_buy=True, investor_id=42
            ),
        ],
        modified_orders=["2"],
        completed_orders=["1"],
    )


def test_market_sell_order__success():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id="5",
                    investor_id=42,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=False,
                )
            ],
            assets=[EngineAsset(investor_id=42, ticker="AAPL", volume=Decimal(1))],
            prices={"AAPL": Decimal(10)},
            balances={42: Decimal(25)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL", volume=Decimal(1), is_buy=False, investor_id=42
            )
        ],
        modified_orders=[],
        completed_orders=["5"],
    )


def test_market_sell_order__decimal_values__success():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id="5",
                    investor_id=42,
                    ticker="AAPL",
                    volume=Decimal(0.3009),
                    is_buy=False,
                )
            ],
            assets=[EngineAsset(investor_id=42, ticker="AAPL", volume=Decimal(0.54))],
            prices={"AAPL": Decimal(100.5)},
            balances={42: Decimal(45.8)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL", volume=Decimal(0.3009), is_buy=False, investor_id=42
            )
        ],
        modified_orders=[],
        completed_orders=["5"],
    )


def test_market_sell_order__decimal_values__sells_partial():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id="5",
                    investor_id=42,
                    ticker="AAPL",
                    volume=Decimal(0.3009),
                    is_buy=False,
                )
            ],
            assets=[
                EngineAsset(investor_id=42, ticker="AAPL", volume=Decimal(0.240001))
            ],
            prices={"AAPL": Decimal(100.5)},
            balances={42: Decimal(45.8)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL", volume=Decimal(0.240001), is_buy=False, investor_id=42
            )
        ],
        modified_orders=["5"],
        completed_orders=[],
    )


def test_order__price_not_given__ignores_order():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id="1",
                    investor_id=42,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=False,
                ),
                MarketEngineOrder(
                    id="2",
                    investor_id=42,
                    ticker="MSFT",
                    volume=Decimal(1),
                    is_buy=False,
                ),
            ],
            assets=[
                EngineAsset(investor_id=42, ticker="AAPL", volume=Decimal(1)),
                EngineAsset(investor_id=42, ticker="MSFT", volume=Decimal(1)),
            ],
            prices={"AAPL": Decimal(10)},
            balances={42: Decimal(100)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL", volume=Decimal(1), is_buy=False, investor_id=42
            )
        ],
        modified_orders=[],
        completed_orders=["1"],
    )


def test_market_sell_order__not_enough_assets__sells_partial():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id="1",
                    investor_id=42,
                    ticker="AAPL",
                    volume=Decimal(10),
                    is_buy=False,
                )
            ],
            assets=[EngineAsset(investor_id=42, ticker="AAPL", volume=Decimal(5))],
            prices={"AAPL": Decimal(10)},
            balances={42: Decimal(100)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL", volume=Decimal(5), is_buy=False, investor_id=42
            )
        ],
        modified_orders=["1"],
        completed_orders=[],
    )


def test_market_two_sell_orders__enough_assets_owned__sells_all():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id="1",
                    investor_id=42,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=False,
                ),
                MarketEngineOrder(
                    id="2",
                    investor_id=42,
                    ticker="AAPL",
                    volume=Decimal(3),
                    is_buy=False,
                ),
            ],
            assets=[EngineAsset(investor_id=42, ticker="AAPL", volume=Decimal(5))],
            prices={"AAPL": Decimal(10)},
            balances={42: Decimal(100)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL", volume=Decimal(1), is_buy=False, investor_id=42
            ),
            EngineTransaction(
                ticker="AAPL", volume=Decimal(3), is_buy=False, investor_id=42
            ),
        ],
        modified_orders=[],
        completed_orders=["1", "2"],
    )


def test_market_two_sell_orders__not_enough_assets_owned__one_partial():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(
                    id="1",
                    investor_id=42,
                    ticker="AAPL",
                    volume=Decimal(1),
                    is_buy=False,
                ),
                MarketEngineOrder(
                    id="2",
                    investor_id=42,
                    ticker="AAPL",
                    volume=Decimal(3),
                    is_buy=False,
                ),
            ],
            assets=[EngineAsset(investor_id=42, ticker="AAPL", volume=Decimal(2))],
            prices={"AAPL": Decimal(10)},
            balances={42: Decimal(100)},
        ),
        transactions=[
            EngineTransaction(
                ticker="AAPL", volume=Decimal(1), is_buy=False, investor_id=42
            ),
            EngineTransaction(
                ticker="AAPL", volume=Decimal(1), is_buy=False, investor_id=42
            ),
        ],
        modified_orders=["2"],
        completed_orders=["1"],
    )
