from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from modules.chats.models import Chat
from modules.chats.services import (
    ChatMessagesService,
)


class MessageSerializer(serializers.Serializer):
    id = serializers.CharField()
    role = serializers.CharField()
    content = serializers.CharField()
    created_at = serializers.DateTimeField(required=False)
    experimental_attachments = serializers.ListField(required=False)
    tool_invocations = serializers.ListField(required=False)
    parts = serializers.ListField(required=False)

    @staticmethod
    def serialize_message(model_message):
        chat_messages_service = ChatMessagesService()
        return chat_messages_service.to_chat_message(model_message)


class ChatSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ["id", "title", "created_at", "updated_at", "message_count"]
        read_only_fields = ["id", "created_at", "updated_at", "message_count"]

    def get_message_count(self, obj: Chat) -> int:
        return obj.messages.count()


class ChatDetailSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = ["id", "title", "created_at", "updated_at", "messages"]
        read_only_fields = ["id", "created_at", "updated_at", "messages"]

    @extend_schema_field(serializers.ListSerializer(child=MessageSerializer()))
    def get_messages(self, obj: Chat):
        chat_message_service = ChatMessagesService()
        model_messages = chat_message_service.sync_get_messages(obj.id)
        serialized_messages = [
            MessageSerializer.serialize_message(msg) for msg in model_messages
        ]
        return [msg for msg in serialized_messages if msg is not None]


class CreateChatSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    first_message = serializers.CharField(max_length=10000)


class CreateChatMessageSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=10000)
    role = serializers.ChoiceField(choices=["user", "assistant"], default="user")
