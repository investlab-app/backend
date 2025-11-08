from collections.abc import Iterator

from polygon import RESTClient as PolygonClient
from polygon.exceptions import BadResponse
from polygon.rest.models.tickers import Ticker, TickerDetails

from config.clients import polygon_client
from config.settings import POLYGON_ASSET_TYPE, POLYGON_EXCHANGE


class PolygonTickersRepository:
    def __init__(self, client: PolygonClient | None = None):
        self.polygon_client = client or polygon_client

    def list_tickers(
        self,
        market: str = POLYGON_ASSET_TYPE,
        exchange: str = POLYGON_EXCHANGE,
        tickers_per_page: int = 500,
        **kwargs,
    ) -> Iterator[Ticker] | None:
        """List tickers from Polygon API."""
        try:
            return self.polygon_client.list_tickers(
                limit=tickers_per_page,  # Max tickers per one request
                market=market,
                exchange=exchange,
                **kwargs,
            )
        except BadResponse:
            return None

    def get_ticker_details(self, ticker: str) -> TickerDetails | None:
        """Get details of a specific ticker from Polygon API."""
        try:
            return self.polygon_client.get_ticker_details(ticker.upper())
        except BadResponse:
            return None
