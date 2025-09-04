import pytest
from polygon.rest.models.tickers import TickerNews

from modules.core.utils import get_local_datetime
from modules.users.tests.conftest import user  # noqa: F401


@pytest.fixture
def fake_news():
    return [
        TickerNews(
            id=str(i),  # type: ignore
            publisher={"name": "Polygon"},  # type: ignore
            title=f"Test news {i}",  # type: ignore
            author="John Doe",  # type: ignore
            published_utc=get_local_datetime(),  # type: ignore
            article_url=f"https://example.com/article-{i}",  # type: ignore
            description=f"Description {i}",  # type: ignore
            tickers=["AAPL", "MSFT"],  # type: ignore
        )
        for i in range(5)
    ]
