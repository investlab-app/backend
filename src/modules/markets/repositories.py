from cache_memoize import cache_memoize
from polygon import RESTClient as PolygonClient
from polygon.exceptions import BadResponse
from polygon.rest.models.markets import MarketHoliday, MarketStatus

from config.clients import polygon_client


class PolygonMarketsRepository:
    def __init__(self, client: PolygonClient | None = None):
        self.polygon_client = client or polygon_client

    @cache_memoize(60 * 2)  # 2 min
    def list_market_holidays(self) -> list[MarketHoliday] | None:
        """Fetch upcoming market holidays from Polygon API."""
        try:
            return self.polygon_client.get_market_holidays()
        except BadResponse:
            return None

    @cache_memoize(60 * 2)  # 2 min
    def get_market_status(self) -> MarketStatus | None:
        """Fetch current market status from Polygon API."""
        try:
            return self.polygon_client.get_market_status()
        except BadResponse:
            return None
