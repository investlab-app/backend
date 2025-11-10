import pytest
from decimal import Decimal
import json
from config.clients import redis_client
from unittest.mock import MagicMock, patch, call
from modules.graph_lang.framework.actions import (
    BuySellAmountAction,
    BuySellForPriceAction,
    BuySellPercentAction,
    NotificationAction,
    Action,
)
from modules.graph_lang.framework.action_handler import ActionHandler
from modules.investors.tests.conftest import create_fake_investor
from modules.instruments.tests.conftest import create_fake_instrument
from modules.instruments.models import Instrument
from modules.investors.models import Asset, Investor
from modules.graph_lang.models import GraphEffect, BuySellEffect, NotificationEffect
from modules.graph_lang.tests.conftest import fake_graph

pytestmark = pytest.mark.django_db


class TestActionHandler:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.investor = create_fake_investor(save=True)
        self.graph = fake_graph(investor=self.investor, save=True)
        self.instrument = create_fake_instrument(ticker="AAPL", save=True)
        self.order_service = MagicMock()
        self.handler = ActionHandler(self.order_service)

    def handle_default(self, action_set):
        self.handler.handle(
            investor_id=self.investor.id, graph_id=self.graph.id, action_set=action_set
        )

    def set_prices(self, prices):
        redis_client.set('latest_prices', json.dumps(prices))

    def set_assets(self, volume):
        Asset.objects.create(
            investor = self.investor,
            ticker = self.instrument,
            volume = volume
        )

    def clear_prices(self):
        redis_client.delete('latest_prices')

    def buy_amount(self, ticker, amount):
        return BuySellAmountAction(action="buy", amount=Decimal(amount), ticker=ticker)

    def sell_amount(self, ticker, amount):
        return BuySellAmountAction(action="sell", amount=Decimal(amount), ticker=ticker)

    def buy_price(self, ticker, price):
        return BuySellForPriceAction(action='buy', price=Decimal(price), ticker=ticker)
    
    def sell_price(self, ticker, price):
        return BuySellForPriceAction(action='sell', price=Decimal(price), ticker=ticker)

    def buy_percentage(self, ticker, percent):
        return BuySellPercentAction(action='buy', percent=Decimal(percent), ticker=ticker)

    def sell_percentage(self, ticker, percent):
        return BuySellPercentAction(action='sell', percent=Decimal(percent), ticker=ticker)

    def buy_sell_effect_equals(
        self, effect, is_buy, amount, success=True, graph=None, instrument=None
    ):
        graph = graph or self.graph
        instrument = instrument or self.instrument
        return (
            effect.graph == graph
            and effect.success == success
            and effect.effect.instrument == instrument
            and effect.effect.is_buy == is_buy
            and effect.effect.amount == amount
        )


    def test__no_actions_given__nothing_happens(self):
        self.handle_default(action_set={})

    def test__buy_amount_action__calls_buy_service(self):
        self.handle_default(
            action_set={self.buy_amount("AAPL", 1)},
        )

        self.order_service.create.assert_called_once_with(
            investor=self.investor, instrument=self.instrument, volume=1, is_buy=True
        )

    def test__sell_amount_action__calls_order_create_service(self):
        self.handle_default(action_set={self.sell_amount("AAPL", 1)})

        self.order_service.create.assert_called_once_with(
            investor=self.investor, instrument=self.instrument, volume=1, is_buy=False
        )

    def test__buy_sell_multiple_actions__create_multiple_orders(self):
        self.handle_default(
            action_set={
                self.buy_amount(amount=1, ticker="AAPL"),
                self.sell_amount(amount=1, ticker="AAPL"),
            },
        )

        assert self.order_service.create.call_count == 2


    def test__buy_order_create_success__graph_result_entry_is_created(self):
        self.handle_default(
            action_set={self.buy_amount(amount=1, ticker="AAPL")},
        )

        effect = GraphEffect.objects.prefetch_related("effect")[0]

        assert self.buy_sell_effect_equals(effect=effect, is_buy=True, amount=1)

    def test__sell_order_create_success__graph_result_entry_is_created(self):
        self.handle_default(
            action_set={self.sell_amount(amount=10, ticker="AAPL")},
        )

        effect = GraphEffect.objects.prefetch_related("effect")[0]

        assert self.buy_sell_effect_equals(effect=effect, is_buy=False, amount=10)

    def test__buy_sell_order_create_failure__result_success_is_false(self):
        self.order_service.create.return_value = None

        self.handle_default(
            action_set={
                self.buy_amount(ticker="AAPL", amount=10),
                self.sell_amount(amount=10, ticker="AAPL"),
            },
        )

        effect = GraphEffect.objects.all()
        assert len(effect) == 2
        assert effect[0].success == False
        assert effect[1].success == False

    def test__buy_sell_price__service_gets_called(self):
        self.set_prices({'AAPL': 50})
        self.handle_default({self.buy_price('AAPL', 100)})

        self.order_service.create.assert_called_once_with(
            investor = self.investor,
            instrument = self.instrument,
            volume  = 2,
            is_buy = True
        )
        self.clear_prices()

    def test__buy_sell_price__success_effect_is_created(self):
        self.set_prices({'AAPL': 50})
        self.handle_default({self.buy_price('AAPL', 100)})

        assert GraphEffect.objects.all()[0].success

    def test__buy_sell_price__multiple_effects__all_handled(self):
        self.set_prices({'AAPL': 50})

        self.handle_default({self.buy_price('AAPL', 100), self.sell_price('AAPL', 100)})

        assert self.order_service.create.call_count == 2
        assert len(GraphEffect.objects.all()) == 2

    def test__buy_sell_price_fail__failed_effect_is_created(self):
        self.order_service.create.return_value = None
        self.set_prices({'AAPL': 50})

        self.handle_default({self.buy_price('AAPL', 100)})

        assert not GraphEffect.objects.all()[0].success

    def test__buy_percentage__service_gets_called(self):
        self.set_assets(50)
        self.handle_default({self.buy_percentage('AAPL', 0.50)})

        self.order_service.create.assert_called_once_with(
            investor = self.investor,
            instrument = self.instrument,
            volume  = 25,
            is_buy = True
        )

    def test__sell_percentage__service_gets_called(self):
        self.set_assets(50)
        self.handle_default({self.sell_percentage('AAPL', 0.50)})

        self.order_service.create.assert_called_once_with(
            investor = self.investor,
            instrument = self.instrument,
            volume  = 25,
            is_buy = False
        )

    def test__buy_sell_percentage__success_effect_is_created(self):
        self.set_assets(50)
        self.handle_default({self.buy_percentage('AAPL', 0.50)})

        assert GraphEffect.objects.all()[0].success

    def test__buy_sell_percentage__multiple_effects__all_handled(self):
        self.set_assets(50)
        self.handle_default({self.buy_percentage('AAPL', 0.30), self.sell_percentage('AAPL', 1.00),})

        assert self.order_service.create.call_count == 2
        assert len(GraphEffect.objects.all()) == 2

    def test__buy_sell_percentage_fail__failed_effect_is_created(self):
        self.order_service.create.return_value = None
        self.set_assets(50)

        self.handle_default({self.buy_percentage('AAPL', 1.00)})

        assert not GraphEffect.objects.all()[0].success

    def test__volume_is_zero__create_is_not_called(self):
        self.handle_default({self.buy_amount('AAPL', 0)})

        assert self.order_service.create.call_count == 0

    def test__volume_is_zero__failed_effect_is_added(self):
        self.handle_default({self.buy_amount('AAPL', 0)})

        effect = GraphEffect.objects.all()[0]
        assert self.buy_sell_effect_equals(
            effect,
            is_buy=True,
            amount=0,
            success=False
        )

    def test__percentage_is_outside_range__create_not_called(self):
        self.set_assets(100)
        self.handle_default({self.buy_percentage('AAPL', -0.1), 
                             self.buy_percentage('AAPL', 1.1)})

        assert self.order_service.create.call_count == 0

    def test__percentage_is_outside_range__failed_effect_is_added(self):
        self.set_assets(100)
        self.handle_default({self.buy_percentage('AAPL', -0.1)})

        effect = GraphEffect.objects.all()[0]
        assert self.buy_sell_effect_equals(
            effect,
            is_buy=True,
            amount=0,
            success=False
        )




# TODO make 'latest_prices' from redis client constant
# TODO make fixture for redis_client prices
# TODO check ticker case sensitivity