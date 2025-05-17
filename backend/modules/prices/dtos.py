from dataclasses import dataclass
from datetime import datetime

@dataclass
class InstrumentPriceDTO:
    timestamp: datetime
    ticker: str
    open: float
    high: float
    low: float
    close: float
    volume: float
