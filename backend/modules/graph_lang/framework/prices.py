from datetime import datetime
from decimal import Decimal


class PriceProvider:
    def get(self, ticker: str, time_at: datetime) -> Decimal:
        raise NotImplementedError
