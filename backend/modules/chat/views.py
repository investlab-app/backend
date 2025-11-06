from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from modules.chat.models import ChatMessage
from modules.chat.serializers import ChatMessageSerializer
from modules.investors.models import Investor


class ChatHistoryView(APIView):
    """
    Retrieve or clear chat message history for the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve chat message history for the authenticated user.

        Query Parameters:
            limit (int): Maximum number of messages to return (default: 50, max: 100)
            offset (int): Number of messages to skip for pagination (default: 0)

        Returns:
            200: List of chat messages with pagination info
            404: Investor profile not found
        """
        # Get investor instance
        try:
            investor = Investor.objects.get(clerk_id=request.user.id)
        except Investor.DoesNotExist:
            return Response(
                {"error": "Investor profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get pagination parameters
        limit = min(int(request.query_params.get("limit", 50)), 100)
        offset = int(request.query_params.get("offset", 0))

        # Fetch messages
        messages = ChatMessage.objects.filter(investor=investor).order_by(
            "-created_at"
        )[offset : offset + limit]

        # Get total count for pagination
        total_count = ChatMessage.objects.filter(investor=investor).count()

        # Reverse to chronological order (oldest first)
        messages = list(reversed(messages))

        serializer = ChatMessageSerializer(messages, many=True)

        return Response(
            {
                "messages": serializer.data,
                "pagination": {
                    "total": total_count,
                    "limit": limit,
                    "offset": offset,
                    "has_more": (offset + limit) < total_count,
                },
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request):
        """
        Clear all chat messages for the authenticated user.

        Returns:
            204: Messages successfully deleted (no content)
            404: Investor profile not found
        """
        # Get investor instance
        try:
            investor = Investor.objects.get(clerk_id=request.user.id)
        except Investor.DoesNotExist:
            return Response(
                {"error": "Investor profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Delete all messages
        ChatMessage.objects.filter(investor=investor).delete()

        return Response(status=status.HTTP_204_NO_CONTENT)
