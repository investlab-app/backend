from decimal import Decimal
import pytest
from datetime import datetime
import faker
from modules.prices.tests.conftest import PriceRepositoryMock
from modules.instruments.models import Instrument
from modules.transactions.services import TransactionStatsService, TransactionStats
from modules.investors.tests.test_investor_stats import investor_factory
from modules.instruments.tests.conftest import instruments_factory
from modules.transactions.models import Transaction
from modules.core.tests.conftest import year
from modules.transactions.tests.conftest import transaction_factory

fake = faker.Faker()
pytestmark = pytest.mark.django_db


class TestTransactionStats:
    @pytest.fixture(autouse=True)
    def setup(self, investor_factory, instruments_factory):
        self.price_mock = PriceRepositoryMock()
        self.investor = investor_factory()
        self.ticker = instruments_factory()
        self.service = TransactionStatsService(prices_service=self.price_mock)

    @pytest.fixture
    def buy_transaction(self, transaction_factory):
        def create_buy_transaction(**kwargs):
            return transaction_factory(
                investor=self.investor,
                ticker=self.ticker,
                is_buy=True,
                **kwargs,
            )

        return create_buy_transaction

    @pytest.fixture
    def sell_transaction(self, transaction_factory):
        def create_buy_transaction(**kwargs):
            return transaction_factory(
                investor=self.investor,
                ticker=self.ticker,
                is_buy=False,
                **kwargs,
            )

        return create_buy_transaction

    def run_get_stats(self, start_date=None, end_date=None) -> TransactionStats:
        return self.service.get_stats(
            investor=self.investor,
            tickers=[self.ticker],
            start_date=start_date,
            end_date=end_date,
        )[0]

    def test_stats__no_transactions_no_tickers__returns_empty_list(self):
        stats = self.service.get_stats(self.investor)

        assert stats == []

    def test_stats__single_ticker_no_transactions__returns_empty_transaction_stats(
        self,
    ):
        stats = self.service.get_stats(self.investor, tickers=[self.ticker])

        assert stats == [
            TransactionStats(
                ticker=self.ticker.ticker,
                total_buy_volume=0,
                total_buy_price=0,
                total_sell_volume=0,
                total_sell_price=0,
                initial_ticker_price=0,
                initial_ticker_volume=0,
                final_ticker_price=0,
                final_ticker_volume=0,
                buy_transactions=0,
                sell_transactions=0,
                gain=0,
            )
        ]

    def test_stats__n_tickers_no_transactions__returns_n_empty_transaction_stats(
        self, instruments_factory
    ):
        n = 5
        instruments = [instruments_factory() for _ in range(n)]

        stats = self.service.get_stats(self.investor, tickers=instruments)

        assert len(stats) == n

    def test_stats__two_buy_transactions__returns_valid_stats(self, buy_transaction):
        buy_transaction(volume=5, price=20)
        buy_transaction(volume=15, price=5)

        stats: TransactionStats = self.run_get_stats()

        assert stats.total_buy_volume == 20
        assert stats.total_buy_price == 25
        assert stats.buy_transactions == 2

    def test_stats__two_sell_transactions__returns_valid_stats(self, sell_transaction):
        sell_transaction(volume=5, price=20)
        sell_transaction(volume=15, price=5)

        stats: TransactionStats = self.run_get_stats()

        assert stats.total_sell_volume == 20
        assert stats.total_sell_price == 25
        assert stats.sell_transactions == 2

    def test_transactions_outside_time_range__get_ignored(
        self, buy_transaction, sell_transaction, year
    ):
        sell_transaction(volume=5, price=1, date=year(2000))
        buy_transaction(volume=5, price=1, date=year(2000))
        sell_transaction(volume=15, price=10, date=year(2010))
        buy_transaction(volume=15, price=10, date=year(2010))
        sell_transaction(volume=5, price=1, date=year(2020))
        buy_transaction(volume=5, price=1, date=year(2020))

        stats: TransactionStats = self.run_get_stats(
            start_date=year(2005),
            end_date=year(2015),
        )

        assert stats.sell_transactions == 1
        assert stats.buy_transactions == 1

    def test_initial_ticker_volume__n_assets_owned_before__equals_n(
        self, buy_transaction, sell_transaction, year
    ):
        buy_transaction(volume=5, date=year(2000))
        sell_transaction(volume=2, date=year(2000))
        buy_transaction(volume=3, date=year(2000))
        buy_transaction(volume=3, date=year(2020))

        stats: TransactionStats = self.run_get_stats(
            start_date=year(2010),
        )

        assert stats.initial_ticker_volume == 5 - 2 + 3

    def test_final_ticker_volume__n_assets_owned_after_end_date__equals_n(
        self, buy_transaction, sell_transaction, year
    ):
        buy_transaction(volume=15, price=0, date=year(2000))
        buy_transaction(volume=5, price=0, date=year(2010))
        sell_transaction(volume=2, price=0, date=year(2010))
        buy_transaction(volume=3, price=0, date=year(2010))
        buy_transaction(volume=3, price=0, date=year(2020))

        stats: TransactionStats = self.run_get_stats(
            start_date=year(2005),
            end_date=year(2015),
        )

        assert stats.final_ticker_volume == 15 + 5 - 2 + 3

    def test_initial_ticker_price__start_date_specified__contains_valid_price(
        self, year
    ):
        dt = year(2015)
        self.price_mock.raise_exception_on_miss = True
        self.price_mock.set_price(self.ticker, dt, 10)

        stats: TransactionStats = self.run_get_stats(start_date=dt)

        assert stats.initial_ticker_price == 10

    def test_final_ticker_price__end_date_specified__contains_valid_price(self, year):
        dt = year(2025)
        self.price_mock.raise_exception_on_miss = True
        self.price_mock.set_price(self.ticker, dt, 10)

        stats: TransactionStats = self.run_get_stats(end_date=dt)

        assert stats.final_ticker_price == 10

    def test_gain(self, buy_transaction, sell_transaction, year):
        self.price_mock.raise_exception_on_miss = True
        buy_transaction(volume=10, price=5, date=year(2005))
        self.price_mock.set_price(self.ticker, year(2010), 10)
        buy_transaction(volume=5, price=5, date=year(2015))
        sell_transaction(volume=2, price=15, date=year(2015))
        self.price_mock.set_price(self.ticker, year(2020), 20)

        initial_value = 10 * 10
        buys = 5
        sells = 15
        final_value = (10 + 5 - 2) * 20
        gain = final_value - buys + sells - initial_value
        stats: TransactionStats = self.run_get_stats(
            start_date=year(2010),
            end_date=year(2020),
        )

        assert stats.gain == gain
