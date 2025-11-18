from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.response import Response

from modules.chats.models import Chat
from modules.chats.serializers import (
    ChatDetailSerializer,
    ChatSerializer,
    CreateChatMessageSerializer,
    CreateChatSerializer,
)
from modules.chats.tasks import respond_to_chat_message
from modules.investors.models import Investor


class ChatsView(generics.ListCreateAPIView):
    ordering_fields = ["created_at", "updated_at", "title"]
    ordering = ["-updated_at"]
    pagination_class = None

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CreateChatSerializer
        return ChatSerializer

    def get_queryset(self):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        return Chat.objects.filter(investor=investor)

    @extend_schema(responses={201: ChatSerializer})
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        first_message = serializer.validated_data["first_message"]
        # TODO: based on the content we should generate a title using LLM
        title = serializer.validated_data.get("title", first_message[:30])

        chat = Chat.objects.create(investor=investor, title=title)

        respond_to_chat_message.delay(
            investor_id=investor.id,
            chat_id=chat.id,
            user_message=first_message,
        )

        chat_serializer = ChatSerializer(chat)
        return Response(
            chat_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class ChatDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ChatDetailSerializer
    lookup_field = "id"

    def get_queryset(self):
        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        return Chat.objects.filter(investor=investor).prefetch_related("messages")

    def destroy(self, request, *args, **kwargs):
        chat = self.get_object()
        chat.delete()
        return Response(
            status=status.HTTP_204_NO_CONTENT,
        )


class ChatMessageView(generics.CreateAPIView):
    serializer_class = CreateChatMessageSerializer

    @extend_schema(
        responses={
            201: {
                "type": "object",
                "properties": {"status": {"type": "string"}},
            }
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        chat_id = self.kwargs.get("id")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        investor = get_object_or_404(Investor, clerk_id=self.request.user.id)
        chat = get_object_or_404(Chat, id=chat_id, investor=investor)

        respond_to_chat_message.delay(
            investor_id=investor.id,
            chat_id=chat.id,
            user_message=serializer.validated_data["content"],
        )

        return Response(
            {"status": "created"},
            status=status.HTTP_201_CREATED,
        )
