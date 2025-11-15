from django.urls import path

from .views import ChatDetailView, ChatMessageView, ChatsView

urlpatterns = [
    path("", ChatsView.as_view(), name="chats"),
    path("<uuid:id>/", ChatDetailView.as_view(), name="chat-detail"),
    path("<uuid:id>/messages/", ChatMessageView.as_view(), name="chat-messages"),
]
