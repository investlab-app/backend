from itertools import islice

from drf_spectacular.utils import extend_schema
from rest_framework import status, views
from rest_framework.response import Response

from modules.news.repositories import PolygonNewsRepository
from modules.news.serializers import NewsListQueryParams, TickerNewsSerializer


class NewsListView(views.APIView):
    @extend_schema(
        parameters=[NewsListQueryParams],
        responses=TickerNewsSerializer(many=True),
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
            published_utc_lte=validated_data.get("published_utc_lte"),
            published_utc_gte=validated_data.get("published_utc_gte"),
            sort=validated_data.get("sort"),
            order=validated_data.get("order"),
            news_per_page=30,
        )

        if news_iterator is None:
            return Response(
                "Failed to fetch news.", status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        news_list = list(islice(news_iterator, validated_data.get("number_of_news")))
        serialized_news = TickerNewsSerializer(news_list, many=True)

        return Response(serialized_news.data)
