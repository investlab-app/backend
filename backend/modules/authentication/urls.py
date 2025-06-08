from django.urls import path
from modules.authentication.views import ClerkUsernamePasswordSignInView

urlpatterns = [
    path(
        "sign-in/",
        ClerkUsernamePasswordSignInView.as_view(),
        name="clerk-sign-in",
    ),
]
