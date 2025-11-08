from django.urls import path

from modules.news.views import NewsListView

urlpatterns = [
    path("", NewsListView.as_view(), name="news-list"),
]
