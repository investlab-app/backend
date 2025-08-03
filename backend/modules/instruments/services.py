from django.db import transaction
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor

from config.logging import get_logger
from config.polygon import client
from modules.instruments.serializers import TickerOverviewResultSerializer

logger = get_logger(__name__)



class InstrumentServiceV2:
    a = 0

    @staticmethod
    def pull_instrument_details(ticker):
        InstrumentServiceV2.a += 1
        if InstrumentServiceV2.a % 50 == 0:
            print(InstrumentServiceV2.a)
        return asdict(client.get_ticker_details(ticker))

    @staticmethod
    def pull_all_instruments():
        tickers = []
        i = 0
        for t in client.list_tickers(limit=1000):
            tickers.append(t)
            i += 1
            if i % 50 == 0:
                print(i)

        names = [t.ticker for t in tickers]
        results = []
        with ThreadPoolExecutor(max_workers=50) as executor:
            f = InstrumentServiceV2.pull_instrument_details
            results = list(executor.map(f, names))

        serializers = []
        for r in results:
            serializers.append(TickerOverviewResultSerializer(data=r))

        with transaction.atomic():
            for s in serializers:
                if s.is_valid():
                    i = s.save()
                    print(f"Saved {i.ticker}")
                else:
                    print(f'{s.initial_data["ticker"]} is invalid')
                    print(s.errors)

        print(f'Fetched {len(results)} results')