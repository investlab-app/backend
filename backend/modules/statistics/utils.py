from modules.instruments.models import Instrument
from modules.investors.models import Investor
from modules.transactions.models import Transaction


def get_investor_tickers(investor: Investor) -> list[str]:
    return list(
        Instrument.objects.filter(
            id__in=Transaction.objects.filter(investor=investor)
            .values_list("ticker_id", flat=True)
            .distinct()
        )
    )
