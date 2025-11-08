import pytest
from polygon.rest.models.tickers import TickerNews

from modules.authentication.tests.conftest import user
from modules.core.utils import get_local_datetime


@pytest.fixture
def fake_news():
    return [
        TickerNews.from_dict(
            {
                "id": str(i),
                "publisher": {"name": "Polygon"},
                "title": f"Test news {i}",
                "author": "John Doe",
                "published_utc": get_local_datetime(),
                "article_url": f"https://example.com/article-{i}",
                "description": f"Description {i}",
                "tickers": ["AAPL", "MSFT"],
            }
        )
        for i in range(5)
    ]
