import logging

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from modules.chats.models import Chat
from modules.chats.services import ChatMessagesService

logger = logging.getLogger(__name__)


class ChatSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ["id", "title", "created_at", "updated_at", "message_count"]
        read_only_fields = ["id", "created_at", "updated_at", "message_count"]

    def get_message_count(self, obj: Chat) -> int:
        return obj.messages.count()


class ChatMessageSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True, default="")
    role = serializers.ChoiceField(
        choices=["user", "assistant"], read_only=True, default="user"
    )
    content = serializers.CharField(read_only=True, default="")
    createdAt = serializers.DateTimeField(read_only=True, allow_null=True)  # noqa: N815


class ChatDetailSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ["id", "title", "created_at", "updated_at", "messages"]
        read_only_fields = ["id", "created_at", "updated_at", "messages"]

    @extend_schema_field(serializers.ListField(child=ChatMessageSerializer()))
    def get_messages(self, obj: Chat):
        chat_message_service = ChatMessagesService()
        model_messages = chat_message_service.sync_get_messages(obj.id)
        converted_messages = chat_message_service.convert_messages_to_schema(
            model_messages
        )
        return ChatMessageSerializer(converted_messages, many=True).data


class CreateChatSerializer(serializers.Serializer):
    id = serializers.UUIDField(required=True)
    first_message = serializers.CharField(max_length=10000)


class CreateChatMessageSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=10000)
    role = serializers.ChoiceField(choices=["user", "assistant"], default="user")
