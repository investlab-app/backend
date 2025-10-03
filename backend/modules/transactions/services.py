from decimal import Decimal

from modules.instruments.models import Instrument
from modules.investors.models import Investor


def buy(investor: Investor, ticker: Instrument, volume: Decimal, action_price: Decimal):
    raise NotImplementedError


def sell(investor, ticker, volume, action_price):
    raise NotImplementedError
