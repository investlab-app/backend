from rest_framework import serializers

from modules.chat.models import ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for ChatMessage model."""

    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "created_at"]
        read_only_fields = ["id", "created_at"]
