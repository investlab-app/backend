from django.urls import path
from modules.core.views import AuthTestView, UnauthTestView, AdminTestView

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
]