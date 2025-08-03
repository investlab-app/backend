from django.db import transaction
from dataclasses import asdict
from concurrent.futures import ThreadPoolExecutor

from config.polygon import client
from modules.instruments.serializers import TickerOverviewResultSerializer


class InstrumentServiceV2:

    @classmethod
    def pull_all_instruments(cls):
        tickers = [t for t in client.list_tickers(limit=1000)]
        tickers_details = cls._pull_instruments_asynchronously(tickers)
        validated_serializers = cls._serialize_and_validate(tickers_details)
        cls._insert_into_db(validated_serializers)

        return len(validated_serializers)

    @classmethod
    def _pull_instruments_asynchronously(cls, tickers):
        names = [t.ticker for t in tickers]
        results = []
        with ThreadPoolExecutor(max_workers=50) as executor:
            f = InstrumentServiceV2._pull_instrument_details
            results = list(executor.map(f, names))
        return results

    @classmethod
    def _pull_instrument_details(cls, ticker):
        return asdict(client.get_ticker_details(ticker))

    @classmethod
    def _serialize_and_validate(cls, ticker_details):
        serializers = []
        for d in ticker_details:
            serializer = TickerOverviewResultSerializer(data = d)
            if serializer.is_valid():
                serializers.append(serializer)
        return serializers

    @classmethod
    def _insert_into_db(cls, serializers):
        with transaction.atomic():
            for s in serializers:
                s.save()