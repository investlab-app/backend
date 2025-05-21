from django.urls import path
from modules.core.views import AuthTestView, my_secure_view

urlpatterns = [
    # path(
    #     "users_test/",
    #     AuthTestView.as_view(),
    #     name="users_test",
    # ),
     path("secure-check/", my_secure_view, name="secure-check"),
]