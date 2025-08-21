from typing import Iterator

from config.settings import POLYGON_SECRET_KEY, POLYGON_EXCHANGE, POLYGON_ASSET_TYPE
from polygon import RESTClient as PolygonClient
from polygon.rest.models.tickers import Ticker
from urllib3 import HTTPResponse


class SyncInstrumentsService:

    def __init__(
        self, polygon_client: PolygonClient = None
    ):
        self.polygon_client = polygon_client or PolygonClient(POLYGON_SECRET_KEY)

    def list_tickers(
        self, market: str = None, exchange: str = None, limit: int = 100, *args, **kwargs
    ) -> Iterator[Ticker]:
        """List tickers from Polygon API."""

        response = self.polygon_client.list_tickers(
            market=market or POLYGON_ASSET_TYPE,
            exchange=exchange or POLYGON_EXCHANGE,
            limit=limit,
            *args,
            **kwargs
        )
        if isinstance(response, HTTPResponse):
            raise ValueError("Tickers incorrectly fetched from Polygon API")

        return response

