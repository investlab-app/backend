from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from modules.instruments.models import Instrument

@dataclass
class AggregateTransaction:
    ticker :Instrument
    transaction_time :datetime
    volume :Decimal
    buy_price :Decimal
    current_price :Decimal
    volume_sold :Decimal
    sell_price :Decimal
    gain :Decimal
    percentage_gain :Decimal
