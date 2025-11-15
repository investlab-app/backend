from django.urls import path

from modules.core.views import (
    AdminTestView,
    AlpacaTestView,
    AuthTestView,
    PolygonTestView,
    UnauthTestView,
)

urlpatterns = [
    path(
        "admin_test/",
        AdminTestView.as_view(),
        name="admin_test",
    ),
    path(
        "users_test/",
        AuthTestView.as_view(),
        name="users_test",
    ),
    path("all_test/", UnauthTestView.as_view(), name="all_test"),
    path("polygon_test/", PolygonTestView.as_view(), name="polygon_test"),
    path("alpaca_test/", AlpacaTestView.as_view(), name="alpaca_test"),
]
