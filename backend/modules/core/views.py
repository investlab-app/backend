from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import permissions
from modules.authentication.permissions import IsAdmin
from rest_framework.permissions import IsAuthenticated

class StatusView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    serializer_class = None

    def get(self, _):
        return Response({"message": "App is running!"})


class AdminTestView(GenericAPIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        user = request.user
        return Response({
            "message": "Authenticated successfully!",
            "user_email": user.email,
            "user_id": user.id,
        })


class AuthTestView(GenericAPIView):
    def get(self, request):
        user = request.user
        return Response({
            "message": "Authenticated successfully!",
            "user_email": user.email,
            "user_id": user.id,
        })


class UnauthTestView(GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"OK"})
