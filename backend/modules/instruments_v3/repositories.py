from typing import Iterator

from config.settings import POLYGON_SECRET_KEY, POLYGON_EXCHANGE, POLYGON_ASSET_TYPE
from polygon import RESTClient as PolygonClient
from polygon.rest.models.tickers import Ticker, TickerDetails
from urllib3 import HTTPResponse


class PolygonInstrumentsRepository:

    def __init__(
        self, polygon_client: PolygonClient = None
    ):
        self.polygon_client = polygon_client or PolygonClient(POLYGON_SECRET_KEY)

    def list_tickers(
        self,
        market: str = POLYGON_ASSET_TYPE,
        exchange: str = POLYGON_EXCHANGE,
        *args,
        **kwargs,
    ) -> Iterator[Ticker]:
        """List tickers from Polygon API."""

        response = self.polygon_client.list_tickers(
            limit=500,  # Max tickers per one request
            market=market,
            exchange=exchange,
            *args,
            **kwargs
        )
        if isinstance(response, HTTPResponse):
            raise ValueError("Tickers incorrectly fetched from Polygon API")

        return response

    def get_ticker_details(self, ticker: str) -> TickerDetails:
        """Get details of a specific ticker from Polygon API."""
        ticker = ticker.upper()

        response = self.polygon_client.get_ticker_details(ticker)
        if isinstance(response, HTTPResponse):
            raise ValueError(f"Ticker {ticker} details incorrectly fetched from Polygon API")

        return response
