import pytest
from modules.core.utils import get_local_datetime
from polygon.rest.models.tickers import TickerNews
from modules.users.tests.conftest import user  # noqa: F401


@pytest.fixture
def fake_news():
    return [
        TickerNews(
            id=str(i),
            publisher={"name": "Polygon"},
            title=f"Test news {i}",
            author="John Doe",
            published_utc=get_local_datetime(),
            article_url=f"https://example.com/article-{i}",
            description=f"Description {i}",
            tickers=["AAPL", "MSFT"],
        )
        for i in range(5)
    ]
