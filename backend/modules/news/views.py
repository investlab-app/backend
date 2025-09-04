from dataclasses import asdict
from itertools import islice

from modules.news.repositories import PolygonNewsRepository
from rest_framework import views
from rest_framework.response import Response
from rest_framework import status
from modules.news.serializers import NewsListQueryParams
from drf_spectacular.utils import extend_schema


class NewsListView(views.APIView):
    NEWS_NUMBER = 30

    @extend_schema(
        parameters=[NewsListQueryParams],
        responses={200: list[dict]},
        description="Retrieve a list of 30 news articles.",
    )
    def get(self, request, *args, **kwargs):
        serializer = NewsListQueryParams(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data

        repository = PolygonNewsRepository()

        news_iterator = repository.list_news(
            ticker=validated_data.get("ticker"),
            published_utc=validated_data.get("published_utc"),
            published_utc_lt=validated_data.get("published_utc_lt"),
            published_utc_lte=validated_data.get("published_utc_lte"),
            published_utc_gt=validated_data.get("published_utc_gt"),
            published_utc_gte=validated_data.get("published_utc_gte"),
            sort=validated_data.get("sort"),
            order=validated_data.get("order"),
        )

        if news_iterator is None:
            return Response(
                "Failed to fetch news.", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        news_list: list[dict] = [
            asdict(news) for news in islice(news_iterator, self.NEWS_NUMBER)
        ]

        return Response(news_list, status=status.HTTP_200_OK)
