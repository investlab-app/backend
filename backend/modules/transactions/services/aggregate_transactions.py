from datetime import datetime
from modules.investors.models import Investor

from modules.transactions.schemas import AggregateTransaction

def aggregate_transactions(
    investor :Investor,
    start_date :datetime = None,
    end_date :datetime = None,
    tickers :list[str] = None,
) -> list[AggregateTransaction]:
    pass