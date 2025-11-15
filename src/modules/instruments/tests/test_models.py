import pytest

from modules.instruments.models import Instrument

pytestmark = pytest.mark.django_db


class TestInstrumentModel:
    def test_instrument_creation(self, instruments_factory):
        instrument = instruments_factory(ticker="AAPL", name="Apple Inc.")
        assert isinstance(instrument, Instrument)
        assert instrument.pk is not None
        assert instrument.ticker == "AAPL"
        assert instrument.name == "Apple Inc."
