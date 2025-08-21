from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict

from django.db import transaction

from config.clients import polygon_client
from config.settings import POLYGON_ASSET_TYPE, POLYGON_EXCHANGE
from modules.instruments.serializers import TickerOverviewResultSerializer


class InstrumentServiceV2:
    @classmethod
    def pull_all_instruments(cls):
        tickers = polygon_client.list_tickers(market=POLYGON_ASSET_TYPE, exchange=POLYGON_EXCHANGE, limit=1000)
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
        return asdict(polygon_client.get_ticker_details(ticker))  # ty: ignore

    @classmethod
    def _serialize_and_validate(cls, ticker_details):
        serializers = []
        for d in ticker_details:
            serializer = TickerOverviewResultSerializer(data=d)
            if serializer.is_valid():
                serializers.append(serializer)
        return serializers

    @classmethod
    def _insert_into_db(cls, serializers):
        with transaction.atomic():
            for s in serializers:
                s.save()
