from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from config.middleware import clerk_authenticated
class HealthCheckView(GenericAPIView):
    permission_classes = []
    serializer_class = None

    def get(self, _):
        return Response({"message": "App is running!"})


from modules.users.models import User
from rest_framework import permissions, serializers, viewsets

from rest_framework.permissions import IsAuthenticated

from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
@clerk_authenticated
def my_secure_view(request):
    user_details = request.user_details  # Set by your decorator
    return JsonResponse({
        "message": "Authenticated!",
        "user_id": user_details.id,
        "email": user_details.email_addresses[0].email_address,
    })


@clerk_authenticated
class AuthTestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "message": "Authenticated successfully!",
            "user_email": user.email,
            "user_id": user.id,
        })