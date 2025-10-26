from decimal import Decimal
from datetime import datetime

class PriceProvider:
    def get(self, ticker :str, time_at :datetime) -> Decimal:
        raise NotImplementedError()