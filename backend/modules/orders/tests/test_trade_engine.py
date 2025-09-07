from decimal import Decimal
from unittest.mock import Mock

from modules.orders.order_engine.engine import TradeEngine
from modules.orders.order_engine.structures import (
    MarketEngineOrder,
    EngineAsset,
    Transaction,
    TradeEngineInput,
)

def _order_ids_match(orders, ids):
    return {o.id for o in orders} == set(ids)

def _run_test(
    engine_input :TradeEngineInput,
    transactions :list[Transaction],
    modified_orders :list[int],
    completed_orders :list[int],
):
    output_mock = Mock()
    engine = TradeEngine(
        engine_input_fetcher=Mock(side_effect=[engine_input]),
        result_handler=output_mock
    )
    engine.run()

    result = output_mock.call_args.args[0]
    output_mock.assert_called_once()
    assert result.transactions == transactions
    assert _order_ids_match(result.updated_orders, modified_orders)
    assert _order_ids_match(result.completed_orders, completed_orders)

def test_no_orders():
    _run_test(
        engine_input=TradeEngineInput(
            orders = [],
            assets = [],
            prices = {},
            balances={}

        ),

        transactions = [],
        modified_orders=[],
        completed_orders=[]
    )


def test_market_buy_order__not_enough_money():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[MarketEngineOrder(id=1, investor_id="inv_1", ticker="AAPL", volume=1, is_buy=True)],
            assets=[],
            prices={"AAPL": Decimal(10)},
            balances={"inv_1": Decimal(0)}
        ),

        transactions=[],
        modified_orders=[],
        completed_orders=[]
    )


def test_market_buy_order__success():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[MarketEngineOrder(id=5, investor_id="inv_1", ticker="AAPL", volume=1, is_buy=True)],
            assets=[],
            prices={"AAPL": Decimal(10)},
            balances={"inv_1": Decimal(15)}
        ),

        transactions=[Transaction("AAPL", Decimal(1), True, investor_id="inv_1")],
        modified_orders=[],
        completed_orders=[5],
    )


def test_market_sell_order__success():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[MarketEngineOrder(id=5, investor_id="inv_1", ticker="AAPL", volume=1, is_buy=False)],
            assets=[EngineAsset(investor_id="inv_1", ticker="AAPL", volume=1)],
            prices={"AAPL": Decimal(10)},
            balances={"inv_1": Decimal(25)}
        ),

        transactions=[Transaction("AAPL", Decimal(1), False, "inv_1")],
        modified_orders=[],
        completed_orders=[5],
    )


def test_order__price_not_given__ignores_order():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[
                MarketEngineOrder(id=1, investor_id="inv_1", ticker="AAPL", volume=1, is_buy=False),
                MarketEngineOrder(id=2, investor_id="inv_1", ticker="MSFT", volume=1, is_buy=False),
            ],
            assets=[
                EngineAsset(investor_id="inv_1", ticker="AAPL", volume=1),
                EngineAsset(investor_id="inv_1", ticker="MSFT", volume=1),
            ],
            prices={"AAPL": Decimal(10)},
            balances={"inv_1": Decimal(100)}
        ),

        transactions=[Transaction("AAPL", Decimal(1), False, "inv_1")],
        modified_orders=[],
        completed_orders=[1],
    )


def test_market_sell_order__not_enough_assets__sells_partial():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[MarketEngineOrder(id=1, investor_id="inv_1", ticker="AAPL", volume=10, is_buy=False)],
            assets=[EngineAsset(investor_id="inv_1", ticker="AAPL", volume=5)],
            prices={"AAPL": Decimal(10)},
            balances={"inv_1": Decimal(100)}
        ),

        transactions=[Transaction("AAPL", Decimal(5), False, "inv_1")],
        modified_orders=[1],
        completed_orders=[],
    )


def test_market_buy_order__not_enough_money__buys_partial():
    _run_test(
        engine_input=TradeEngineInput(
            orders=[MarketEngineOrder(id=1, investor_id="inv_1", ticker="AAPL", volume=10, is_buy=True)],
            assets=[],
            prices={"AAPL": Decimal(10)},
            balances={"inv_1": Decimal(50)}
        ),

        transactions=[Transaction("AAPL", Decimal(5), True, "inv_1")],
        modified_orders=[1],
        completed_orders=[],
    )