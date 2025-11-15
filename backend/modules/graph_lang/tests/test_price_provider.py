from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock, call

import pytest
from faker import Faker

from modules.graph_lang.framework.price_provider import PriceProvider
from modules.prices.schemas import PriceBar, PriceDaily, PriceDailySummary

fake = Faker()


class TestPriceProvider:
    SAMPLES = 100

    @pytest.fixture(autouse=True)
    def setup(self):
        self.repo = MagicMock()
        self.provider = PriceProvider(self.repo, samples=self.SAMPLES)

    @pytest.fixture()
    def dt(self):
        return fake.date_time()

    def set_price_repository_response(self, price_bars):
        if isinstance(price_bars, list):
            self.repo.get_ohlc.side_effect = (
                lambda ticker,
                date_from,
                date_to,
                interval,
                interval_multiplier: price_bars
            )
        else:
            self.repo.get_ohlc.side_effect = (
                lambda ticker,
                date_from,
                date_to,
                interval,
                interval_multiplier: price_bars[ticker]
            )

    def set_price_repository_snapshot_response(self, price_daily_summary):
        self.repo.get_price.side_effect = lambda ticker: price_daily_summary

    def price_bar(self, dt, price):
        return PriceBar(
            dt,
            open=Decimal(0),
            high=Decimal(0),
            low=Decimal(0),
            close=price,
            volume=Decimal(0),
        )

    def price_daily_summary(self, ticker, price):
        return PriceDailySummary(
            ticker=ticker,
            current_price=Decimal(price),
            daily_summary=PriceDaily(
                open=Decimal(0),
                high=Decimal(0),
                low=Decimal(0),
                close=Decimal(0),
                volume=Decimal(0),
                volume_weighted_average_price=Decimal(0),
            ),
            todays_change=Decimal(0),
            todays_change_percent=Decimal(0),
            last_updated=fake.date_time(),
        )

    def test__prefetch_data__no_data__nothing_happens(self, dt):
        self.provider.prefetch_data({}, dt)

    def test__no_prefetch__get_price_raises_value_error(self, dt):
        with pytest.raises(ValueError):
            self.provider.get_price("AAPL", dt)

    def test__prefetch_single_ticker__get_other_ticker__raises(self, dt):
        self.provider.prefetch_data({"AAPL": timedelta()}, dt)

        with pytest.raises(ValueError):
            self.provider.get_price("HEHE", dt)

    @pytest.mark.parametrize("timespan", [timedelta(days=2), timedelta(days=-2)])
    def test__prefetch_single_ticker__price_outside_time_range__raises(
        self, timespan, dt
    ):
        self.provider.prefetch_data({"AAPL": timedelta(days=1)}, dt)

        with pytest.raises(ValueError):
            self.provider.get_price("AAPL", dt + timespan)

    def test__prefetch_single_ticker__returns_price_from_price_repo(self, dt):
        self.set_price_repository_response([self.price_bar(dt, 100)])

        self.provider.prefetch_data({"AAPL": timedelta()}, dt)

        assert self.provider.get_price("AAPL", dt) == 100

    def test__single_ticker__repo_returns_inexact_datetime__price_gets_returned(
        self, dt
    ):
        self.set_price_repository_response(
            [self.price_bar(dt - timedelta(days=1), 100)]
        )

        self.provider.prefetch_data({"AAPL": timedelta(days=1)}, dt)

        assert self.provider.get_price("AAPL", dt) == 100

    def test__get_price__repo_returns_two_datetimes__closest_price_is_returned(
        self, dt
    ):
        self.set_price_repository_response(
            [
                self.price_bar(dt - timedelta(days=1), 100),
                self.price_bar(dt - timedelta(days=5), 200),
            ]
        )

        self.provider.prefetch_data({"AAPL": timedelta(days=7)}, dt)

        assert self.provider.get_price("AAPL", dt) == 100
        assert self.provider.get_price("AAPL", dt - timedelta(days=1)) == 100
        assert self.provider.get_price("AAPL", dt - timedelta(days=4)) == 200
        assert self.provider.get_price("AAPL", dt - timedelta(days=7)) == 200

    def test__get_price__two_tickers__returns_correct_price_for_ticker(self, dt):
        self.set_price_repository_response(
            {"AAPL": [self.price_bar(dt, 100)], "GOGL": [self.price_bar(dt, 200)]}
        )

        self.provider.prefetch_data({"AAPL": timedelta(), "GOGL": timedelta()}, dt)

        assert self.provider.get_price("AAPL", dt) == 100
        assert self.provider.get_price("GOGL", dt) == 200

    def test__repository_function_gets_called_with_correct_args(self, dt):
        self.set_price_repository_response(
            {"AAPL": [self.price_bar(dt, 100)], "GOGL": [self.price_bar(dt, 200)]}
        )

        self.provider.prefetch_data(
            {"AAPL": timedelta(seconds=100), "GOGL": timedelta(seconds=250)}, dt
        )

        self.repo.get_ohlc.assert_has_calls(
            [
                call(
                    "AAPL",
                    dt - timedelta(minutes=15, seconds=100),
                    dt - timedelta(minutes=15),
                    "second",
                    1,
                ),
                call(
                    "GOGL",
                    dt - timedelta(minutes=15, seconds=250),
                    dt - timedelta(minutes=15),
                    "second",
                    2,
                ),
            ]
        )

    def test__get_prices_returned_empty_list__price_is_from_snapshot(self, dt):
        self.set_price_repository_response([])
        self.set_price_repository_snapshot_response(
            self.price_daily_summary("AAPL", 100)
        )

        self.provider.prefetch_data({"AAPL": timedelta()}, dt)

        assert self.provider.get_price("AAPL", dt) == 100
        self.repo.get_price.assert_called_once_with("AAPL")
