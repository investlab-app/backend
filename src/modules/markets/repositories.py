from polygon import RESTClient as PolygonClient
from polygon.exceptions import BadResponse
from polygon.rest.models.markets import MarketHoliday, MarketStatus

from config.clients import polygon_client


class PolygonMarketsRepository:
    def __init__(self, client: PolygonClient | None = None):
        self.polygon_client = client or polygon_client

    def list_market_holidays(self) -> list[MarketHoliday] | None:
        """Fetch upcoming market holidays from Polygon API."""
        try:
            return self.polygon_client.get_market_holidays()
        except BadResponse:
            return None

    def get_market_status(self) -> MarketStatus | None:
        """Fetch current market status from Polygon API."""
        try:
            return self.polygon_client.get_market_status()
        except BadResponse:
            return None

    def is_nasdaq_open(self) -> bool | None:
        """Check if NASDAQ market is currently open."""
        status = self.get_market_status()
        if status is None:
            return None
        return status.exchanges.nasdaq == "open"
