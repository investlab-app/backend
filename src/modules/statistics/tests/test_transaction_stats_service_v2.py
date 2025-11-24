# ruff: noqa: FBT003
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from modules.instruments.models import Instrument
from modules.investors.models import Investor
from modules.prices.services import LatestPriceService
from modules.statistics.services.transaction_stats_service_v2 import (
    TransactionStatsService,
)
from modules.transactions.models import Transaction

pytestmark = pytest.mark.django_db


@pytest.fixture
def investor():
    return Investor.objects.create(clerk_id="clerk_test_id")


@pytest.fixture
def instrument():
    return Instrument.objects.create(ticker="TEST")


@pytest.fixture
def mock_price_service(monkeypatch):
    """Mock LatestPriceService.get_prices_default_dict()"""

    class MockLatestPriceService:
        def get_prices_default_dict(self):
            return {"TEST": Decimal(210)}

    return MockLatestPriceService()


@pytest.fixture
def add_tx(investor, instrument):
    """Helper to add transactions easily."""

    def _add(is_buy, volume, price, ts):
        return Transaction.objects.create(
            investor=investor,
            ticker=instrument,
            volume=Decimal(str(volume)),
            price=Decimal(str(price)),
            is_buy=is_buy,
            timestamp=ts,
        )

    return _add


def test_basic_fifo_gain(investor, instrument, mock_price_service, add_tx):
    """
    BUY 3 @200
    BUY 2 @230
    SELL 4 @220   → gain = 880 - 830 = 50
    """

    t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    add_tx(True, 3, 200, t0)
    add_tx(True, 2, 230, t0 + timedelta(minutes=1))
    add_tx(False, 4, 220, t0 + timedelta(minutes=2))

    txs = Transaction.objects.filter(investor=investor, ticker=instrument)

    svc = TransactionStatsService(
        txs,
        ticker="TEST",
        lastest_price_service=mock_price_service,
    )

    stats = svc.compute_stats()

    assert stats["realized_gain"] == Decimal(50)
    assert stats["remaining_volume"] == Decimal(1)  # 1 from the second lot


def test_unrealized_gain_lifo(db, investor, instrument, mock_price_service, add_tx):
    """
    BUY 2 @230
    BUY 0.5 @210
    price now = 210

    unrealized = 2.5 * 210 - (2 * 230 + 0.5 * 210) = -40
    """

    t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    add_tx(True, 2, 230, t0)
    add_tx(True, 0.5, 210, t0 + timedelta(minutes=1))

    txs = Transaction.objects.all()

    svc = TransactionStatsService(
        txs,
        ticker="TEST",
        lastest_price_service=mock_price_service,
    )

    stats = svc.compute_stats()
    assert stats["unrealized_gain"] == Decimal(-40)


def test_compute_stats_in_period_with_previous_holdings(
    investor, instrument, mock_price_service, add_tx
):
    """
    BEFORE PERIOD:
        BUY 3 @200
        BUY 2 @230

    PERIOD:
        SELL 4 @220  → should consume FIFO (3 @200 + 1 @230)
    """

    t0 = datetime(2023, 12, 31, tzinfo=timezone.utc)
    add_tx(True, 3, 200, t0)
    add_tx(True, 2, 230, t0 + timedelta(minutes=1))

    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 12, 31, tzinfo=timezone.utc)

    add_tx(False, 4, 220, start + timedelta(minutes=1))

    txs = Transaction.objects.filter(investor=investor, ticker=instrument)
    svc = TransactionStatsService(
        txs,
        ticker="TEST",
        lastest_price_service=mock_price_service,
    )

    stats = svc.compute_stats_in_period(start, end)

    # Realized gain: same as normal FIFO: (4*220) - (3*200 + 1*230) = 880 - 830 = 50
    assert stats["realized_gain"] == Decimal(50)

    # Remaining lots after period = 1 share from the second BUY lot
    assert stats["remaining_volume"] == Decimal(1)


def test_period_respects_virtual_lots(investor, instrument, mock_price_service, add_tx):
    """
    BEFORE PERIOD:
        BUY 10 @100
        SELL 5 @120   -> remaining 5 with cost basis 100

    PERIOD:
        SELL 3 @150   -> FIFO sells 3 from the remaining pre-period lots
    """

    t0 = datetime(2023, 12, 31, tzinfo=timezone.utc)
    add_tx(True, 10, 100, t0)
    add_tx(False, 5, 120, t0 + timedelta(minutes=1))

    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = start + timedelta(days=365)

    add_tx(False, 3, 150, start + timedelta(minutes=1))

    txs = Transaction.objects.filter(investor=investor, ticker=instrument)

    svc = TransactionStatsService(
        txs,
        ticker="TEST",
        lastest_price_service=mock_price_service,
    )

    stats = svc.compute_stats_in_period(start, end)

    # Realized gain in PERIOD:
    # sells 3 @150 from virtual remaining lots cost basis 100
    # gain = 3 * 150 - 3 * 100 = 150
    assert stats["realized_gain"] == Decimal(150)

    # Remaining after period: 5 - 3 = 2 shares
    assert stats["remaining_volume"] == Decimal(2)


def test_period_does_not_count_pre_period_realized_gains(
    investor, instrument, mock_price_service, add_tx
):
    """
    Make sure gains before the window DO NOT appear in period stats.
    """

    t0 = datetime(2023, 6, 1, tzinfo=timezone.utc)
    add_tx(True, 5, 100, t0)
    add_tx(False, 5, 110, t0 + timedelta(minutes=1))  # +50 gain

    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 12, 31, tzinfo=timezone.utc)

    txs = Transaction.objects.all()

    svc = TransactionStatsService(
        txs,
        ticker="TEST",
        lastest_price_service=mock_price_service,
    )

    stats = svc.compute_stats_in_period(start, end)

    # No transactions inside the window
    assert stats["realized_gain"] == 0
    assert stats["unrealized_gain"] == 0
    assert stats["total_gain"] == 0
