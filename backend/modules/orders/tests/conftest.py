import pytest

from modules.investors.models import Investor
from modules.instruments.models import Instrument

@pytest.fixture
def investor():
    investor = Investor(balance = 0)
    return investor

@pytest.fixture
def ticker():
    return Instrument(ticker="AAPL")