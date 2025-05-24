from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework import response

class HealthCheckView(GenericAPIView):
    permission_classes = []
    serializer_class = None

    def get(self, _):
        return Response({"message": "App is running!"})


from rest_framework.permissions import IsAuthenticated
from config.permissions import IsAdmin


class AdminTestView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        user = request.user
        return Response({
            "message": "Authenticated successfully!",
            "user_email": user.email,
            "user_id": user.id,
        })


class AuthTestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "message": "Authenticated successfully!",
            "user_email": user.email,
            "user_id": user.id,
        })


class UnauthTestView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        return Response({"OK"})
