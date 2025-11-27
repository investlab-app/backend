# ruff: noqa: FBT003
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from modules.statistics.services.transaction_stats_service_v2 import (
    MultipleInstrumentsTransactionStatsService,
    TransactionStatsService,
)
from modules.transactions.models import Transaction

pytestmark = pytest.mark.django_db


@pytest.fixture
def instrument(instruments_factory):
    return instruments_factory(ticker="TTWO")


@pytest.fixture
def mock_latest_price_service(monkeypatch):
    """Mock LatestPriceService.get_prices_default_dict()"""

    class MockLatestPriceService:
        def get_prices_default_dict(self):
            return {"TTWO": Decimal(210), "FOO": Decimal(60)}

    return MockLatestPriceService()


@pytest.fixture
def mock_polygon_price_repository(monkeypatch):
    """Mock PolygonPricesRepository.get_price_at()"""

    class MockPolygonPricesRepository:
        def get_price_at(self, ticker, timestamp):
            if ticker == "TTWO":
                return Decimal(190)
            elif ticker == "FOO":
                return Decimal(50)
            return None

    return MockPolygonPricesRepository()


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


def test_basic_fifo_gain(
    investor,
    instrument,
    mock_latest_price_service,
    mock_polygon_price_repository,
    add_tx,
):
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
        ticker="TTWO",
        lastest_price_service=mock_latest_price_service,
        polygon_prices_repository=mock_polygon_price_repository,
    )

    stats = svc.compute_stats()

    assert stats.realized_gain == Decimal(50)
    assert stats.remaining_volume == Decimal(1)  # 1 from the second lot
    # total sell cost = 4 * 220 = 880
    assert stats.total_sell_cost == Decimal(880)


def test_unrealized_gain_lifo(
    investor,
    instrument,
    mock_latest_price_service,
    mock_polygon_price_repository,
    add_tx,
):
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
        ticker="TTWO",
        lastest_price_service=mock_latest_price_service,
        polygon_prices_repository=mock_polygon_price_repository,
    )

    stats = svc.compute_stats()
    assert stats.unrealized_gain == Decimal(-40)
    assert stats.total_sell_cost == Decimal(0)


def test_compute_stats_in_period_with_previous_holdings(
    investor,
    instrument,
    mock_latest_price_service,
    mock_polygon_price_repository,
    add_tx,
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
        ticker="TTWO",
        lastest_price_service=mock_latest_price_service,
        polygon_prices_repository=mock_polygon_price_repository,
    )

    stats = svc.compute_stats_in_period(start, end)

    # Realized gain: same as normal FIFO: (4*220) - (3*200 + 1*230) = 880 - 830 = 50
    assert stats.realized_gain == Decimal(50)

    # Remaining lots after period = 1 share from the second BUY lot
    assert stats.remaining_volume == Decimal(1)
    # one sell in period: 4 * 220 = 880
    assert stats.total_sell_cost == Decimal(880)


def test_period_respects_virtual_lots(
    investor,
    instrument,
    mock_latest_price_service,
    mock_polygon_price_repository,
    add_tx,
):
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
        ticker="TTWO",
        lastest_price_service=mock_latest_price_service,
        polygon_prices_repository=mock_polygon_price_repository,
    )

    stats = svc.compute_stats_in_period(start, end)

    # Realized gain in PERIOD:
    # sells 3 @150 from virtual remaining lots cost basis 100
    # gain = 3 * 150 - 3 * 100 = 150
    assert stats.realized_gain == Decimal(150)

    # Remaining after period: 5 - 3 = 2 shares
    assert stats.remaining_volume == Decimal(2)
    # one sell in period of 3 @150 -> 450
    assert stats.total_sell_cost == Decimal(450)


def test_period_does_not_count_pre_period_realized_gains(
    investor,
    instrument,
    mock_latest_price_service,
    mock_polygon_price_repository,
    add_tx,
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
        ticker="TTWO",
        lastest_price_service=mock_latest_price_service,
        polygon_prices_repository=mock_polygon_price_repository,
    )

    stats = svc.compute_stats_in_period(start, end)

    # No transactions inside the window
    assert stats.realized_gain == 0
    assert stats.unrealized_gain == 0
    assert stats.total_gain == 0
    assert stats.total_sell_cost == Decimal(0)


def test_complex_realized_unrealized(
    investor,
    instrument,
    mock_latest_price_service,
    mock_polygon_price_repository,
    add_tx,
):
    """
    Scenariusz opisany w legendzie:
    BUY 3x @200
    BUY 2x @230
    SELL 5x @210
    BUY 1x @210
    SELL 0.5x @220
    BUY 2x @230
    Obecnie @210
    """
    t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)

    add_tx(True, 3, 200, t0)
    add_tx(True, 2, 230, t0 + timedelta(minutes=1))
    add_tx(False, 5, 210, t0 + timedelta(minutes=2))
    add_tx(True, 1, 210, t0 + timedelta(minutes=3))
    add_tx(False, 0.5, 220, t0 + timedelta(minutes=4))
    add_tx(True, 2, 230, t0 + timedelta(minutes=5))

    txs = Transaction.objects.all()
    svc = TransactionStatsService(
        txs,
        ticker="TTWO",
        lastest_price_service=mock_latest_price_service,
        polygon_prices_repository=mock_polygon_price_repository,
    )
    stats = svc.compute_stats()

    assert stats.realized_gain == Decimal(-5)
    assert stats.unrealized_gain == Decimal(-40)
    assert stats.total_gain == Decimal(-45)
    # New total_gain_pct formula
    # total_sell_cost = 5*210 + 0.5*220 = 1160
    # unrealized_gain = -40
    # denominator total_buy_cost = 1730
    assert stats.total_gain_pct == pytest.approx(
        (Decimal(1160) + Decimal(-40)) / Decimal(1730) - Decimal(1)
    )
    assert stats.remaining_volume == Decimal("2.5")
    # sells: 5 @210 and 0.5 @220 => 5*210 + 0.5*220 = 1160
    assert stats.total_sell_cost == Decimal(1160)


def test_partial_sell_percentage(
    investor,
    instrument,
    mock_latest_price_service,
    mock_polygon_price_repository,
    add_tx,
):
    """
    TTWO procentowego zysku/straty dla częściowego sella
    BUY 3x @200
    SELL 1.5x @220
    """
    t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    add_tx(True, 3, 200, t0)
    add_tx(False, 1.5, 220, t0 + timedelta(minutes=1))

    txs = Transaction.objects.all()
    svc = TransactionStatsService(
        txs,
        ticker="TTWO",
        lastest_price_service=mock_latest_price_service,
        polygon_prices_repository=mock_polygon_price_repository,
    )
    stats = svc.compute_stats()

    # gain = 1.5 * 220 - 1.5 * 200 = 30
    assert stats.realized_gain == Decimal(30)
    # remaining 1.5x @200, unrealized gain = 1.5*(210-200)=15
    assert stats.unrealized_gain == Decimal(15)
    assert stats.total_gain == Decimal(45)
    # sell 1.5 @220 => 330
    assert stats.total_sell_cost == Decimal(330)


def test_multiple_sells_fifo(
    investor,
    instrument,
    mock_latest_price_service,
    mock_polygon_price_repository,
    add_tx,
):
    """
    - BUY 2x @100
    - BUY 3x @120
    - SELL 2x @130
    - SELL 2x @140
    - Obecna cena: 210 (z mock_price_service)
    """
    t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)

    add_tx(True, 2, 100, t0)
    add_tx(True, 3, 120, t0 + timedelta(minutes=1))
    add_tx(False, 2, 130, t0 + timedelta(minutes=2))
    add_tx(False, 2, 140, t0 + timedelta(minutes=3))

    txs = Transaction.objects.all()

    svc = TransactionStatsService(
        txs,
        ticker="TTWO",
        lastest_price_service=mock_latest_price_service,
        polygon_prices_repository=mock_polygon_price_repository,
    )

    stats = svc.compute_stats()

    # realized gain:
    # First SELL 2x130 from 2x100 → gain = 2*(130-100)=60
    # Second SELL 2x140 from 2x120 → gain = 2*(140-120)=40
    # Total realized = 60 + 40 = 100
    assert stats.realized_gain == Decimal(100)
    assert stats.unrealized_gain == Decimal(90)
    assert stats.total_gain == Decimal(190)
    # sells: 2*130 + 2*140 = 540
    assert stats.total_sell_cost == Decimal(540)


def test_compute_stats_in_period_edge_case(
    investor,
    instrument,
    mock_latest_price_service,
    mock_polygon_price_repository,
    add_tx,
):
    """
    Okno czasowe: upewniamy się, że pre-okresowe BUYy są brane pod uwagę
    BUY 5x @100 (przed start)
    SELL 3x @110 (okno)
    """
    t0 = datetime(2023, 12, 31, tzinfo=timezone.utc)
    add_tx(True, 5, 100, t0)

    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 12, 31, tzinfo=timezone.utc)
    add_tx(False, 3, 110, start + timedelta(minutes=1))

    txs = Transaction.objects.all()
    svc = TransactionStatsService(
        txs,
        ticker="TTWO",
        lastest_price_service=mock_latest_price_service,
        polygon_prices_repository=mock_polygon_price_repository,
    )
    stats = svc.compute_stats_in_period(start, end)

    # realized gain in period = 3*110 - 3*100 = 30
    assert stats.realized_gain == Decimal(30)
    # remaining 2x 100, unrealized = 2*(190-100)=180
    assert stats.unrealized_gain == Decimal(180)
    assert stats.total_gain == Decimal(210)
    # sell in period: 3 * 110 = 330
    assert stats.total_sell_cost == Decimal(330)


def test_compute_stats_in_period_without_start(
    investor,
    instrument,
    mock_latest_price_service,
    mock_polygon_price_repository,
    add_tx,
):
    """
    When `start` is omitted (None), the period should start from the beginning.

    BUY 3 @200
    SELL 2 @220  (inside window by specifying `end` only)
    """

    t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)
    add_tx(True, 3, 200, t0)
    add_tx(False, 2, 220, t0 + timedelta(minutes=1))

    end = t0 + timedelta(minutes=1)

    txs = Transaction.objects.filter(investor=investor, ticker=instrument)

    svc = TransactionStatsService(
        txs,
        ticker="TTWO",
        lastest_price_service=mock_latest_price_service,
        polygon_prices_repository=mock_polygon_price_repository,
    )

    stats = svc.compute_stats_in_period(end=end)

    # realized gain = 2*220 - 2*200 = 40
    assert stats.realized_gain == Decimal(40)
    # remaining 1 share
    assert stats.remaining_volume == Decimal(1)
    assert stats.total_sell_cost == Decimal(440)  # 2 * 220? WAIT - need to recalc


def test_compute_stats_in_period_without_end(
    investor,
    instrument,
    mock_latest_price_service,
    mock_polygon_price_repository,
    add_tx,
):
    """
    When `end` is omitted (None), the period should go until the latest transaction.

    BEFORE START:
        BUY 5 @100

    PERIOD (start provided):
        SELL 3 @110
    """

    t0 = datetime(2023, 12, 31, tzinfo=timezone.utc)
    add_tx(True, 5, 100, t0)

    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    add_tx(False, 3, 110, start + timedelta(minutes=1))

    txs = Transaction.objects.all()
    svc = TransactionStatsService(
        txs,
        ticker="TTWO",
        lastest_price_service=mock_latest_price_service,
        polygon_prices_repository=mock_polygon_price_repository,
    )

    stats = svc.compute_stats_in_period(start=start)

    # realized gain in period = 3*110 - 3*100 = 30
    assert stats.realized_gain == Decimal(30)
    # remaining 2x 100, unrealized = 2*(210-100)=220
    assert stats.unrealized_gain == Decimal(220)
    assert stats.total_gain == Decimal(250)


def test_transaction_multiple_instruments_stats_service_no_period(
    investor,
    instruments_factory,
    mock_latest_price_service,
    mock_polygon_price_repository,
):
    """
    Ensure stats are computed per-instrument when no period bounds are provided.
    """

    # Create two instruments
    inst1 = instruments_factory(ticker="TTWO")
    inst2 = instruments_factory(ticker="FOO")

    t0 = datetime(2024, 1, 1, tzinfo=timezone.utc)

    # Add transactions for both instruments
    Transaction.objects.create(
        investor=investor,
        ticker=inst1,
        volume=Decimal(2),
        price=Decimal(100),
        is_buy=True,
        timestamp=t0,
    )

    Transaction.objects.create(
        investor=investor,
        ticker=inst2,
        volume=Decimal(1),
        price=Decimal(50),
        is_buy=True,
        timestamp=t0,
    )

    svc = MultipleInstrumentsTransactionStatsService(
        investor=investor,
        instruments=[inst1, inst2],
        lastest_price_service=mock_latest_price_service,
        polygon_prices_repository=mock_polygon_price_repository,
    )

    stats = svc.compute_stats()

    assert set(stats.keys()) == {"TTWO", "FOO"}
    assert stats["TTWO"].remaining_volume == Decimal(2)
    assert stats["TTWO"].end_period_price == Decimal(210)
    assert stats["FOO"].remaining_volume == Decimal(1)
    assert stats["FOO"].end_period_price == Decimal(60)


def test_transaction_multiple_instruments_stats_service_with_period(
    investor,
    instruments_factory,
    mock_latest_price_service,
    mock_polygon_price_repository,
):
    """
    Ensure per-instrument period stats use the polygon repository price at `end`.
    """

    inst1 = instruments_factory(ticker="TTWO")
    inst2 = instruments_factory(ticker="FOO")

    t0 = datetime(2023, 12, 31, tzinfo=timezone.utc)
    Transaction.objects.create(
        investor=investor,
        ticker=inst1,
        volume=Decimal(5),
        price=Decimal(100),
        is_buy=True,
        timestamp=t0,
    )

    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 12, 31, tzinfo=timezone.utc)

    Transaction.objects.create(
        investor=investor,
        ticker=inst1,
        volume=Decimal(3),
        price=Decimal(110),
        is_buy=False,
        timestamp=start + timedelta(minutes=1),
    )

    svc = MultipleInstrumentsTransactionStatsService(
        investor=investor,
        instruments=[inst1, inst2],
        lastest_price_service=mock_latest_price_service,
        polygon_prices_repository=mock_polygon_price_repository,
    )

    stats = svc.compute_stats(start=start, end=end)

    assert set(stats.keys()) == {"TTWO", "FOO"}
    assert stats["TTWO"].end_period_price == Decimal(190)
    assert stats["TTWO"].realized_gain == Decimal(30)
    assert stats["FOO"].end_period_price == Decimal(50)
    assert stats["FOO"].realized_gain == Decimal(0)
