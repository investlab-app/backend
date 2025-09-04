from collections.abc import Iterator

from polygon import RESTClient as PolygonClient
from polygon.exceptions import BadResponse
from polygon.rest.models.tickers import TickerNews

from config.settings import POLYGON_SECRET_KEY


class PolygonNewsRepository:
    def __init__(self, polygon_client: PolygonClient = None):  # type: ignore
        self.polygon_client = polygon_client or PolygonClient(POLYGON_SECRET_KEY)

    def list_news(
        self,
        ticker: str = None,  # type: ignore
        published_utc: str = None,  # type: ignore
        published_utc_lt: str = None,  # type: ignore
        published_utc_lte: str = None,  # type: ignore
        published_utc_gt: str = None,  # type: ignore
        published_utc_gte: str = None,  # type: ignore
        sort: str = None,  # type: ignore
        order: str = None,  # type: ignore
        news_per_page: int = 30,
        **kwargs,
    ) -> Iterator[TickerNews] | None:
        """List tickers from Polygon API.
        - default `sort` is by published_utc
        - default `order` is desc
        """
        try:
            return self.polygon_client.list_ticker_news(
                ticker=ticker.upper() if ticker else None,
                published_utc=published_utc,
                published_utc_lt=published_utc_lt,
                published_utc_lte=published_utc_lte,
                published_utc_gt=published_utc_gt,
                published_utc_gte=published_utc_gte,
                sort=sort,
                order=order,
                limit=news_per_page,  # Max news per one request
                **kwargs,
            )
        except BadResponse:
            return None
