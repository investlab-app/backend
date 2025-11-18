from clerk_backend_api import (
    CreateSessionRequestBodyTypedDict,
    GetUserListRequestTypedDict,
)
from clerk_backend_api.models import SDKError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from config.clients import clerk_client as clerk_sdk
from modules.authentication.serializers import ClerkLoginSerializer


@method_decorator(csrf_exempt, name="dispatch")
class ClerkUsernamePasswordSignInView(APIView):
    """
    Handles Clerk authentication via username (email) and password.
    Returns a Clerk sign-in token upon successful authentication.
    """

    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = ClerkLoginSerializer

    @extend_schema(
        request=ClerkLoginSerializer,
        responses={
            200: OpenApiResponse(description="Sign-in successful, token returned."),
            400: OpenApiResponse(description="Invalid credentials or user not found."),
            401: OpenApiResponse(description="Password verification failed."),
            500: OpenApiResponse(
                description="Clerk SDK error or other internal server error.",
            ),
        },
        summary="Sign in a user with email and password via Clerk",
        description=(
            "Authenticates a user using their email and password through Clerk, "
            "returning a sign-in token upon success."
        ),
    )
    def post(self, request):
        """
        Sign in a user with email and password via Clerk.
        """
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        users = clerk_sdk.users.list(
            request=GetUserListRequestTypedDict(email_address=[email]),
        )
        if not users or len(users) < 1:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        our_user = users[0]
        try:
            clerk_sdk.users.verify_password(user_id=our_user.id, password=password)
        except SDKError as e:
            return Response(
                f"{e.message}: Password did not pass verification",
                status=status.HTTP_401_UNAUTHORIZED,
            )

        session = clerk_sdk.sessions.create(
            request=CreateSessionRequestBodyTypedDict(user_id=our_user.id),
        )

        if session is None:
            return Response(
                {"message": "Session not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        access_token = clerk_sdk.sessions.create_token(
            session_id=session.id,
            expires_in_seconds=600,
        )

        if access_token is None:
            return Response(
                {"message": "Failed to create access token"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "message": "Sign-in successful",
                "session_id": session.id,
                "access_token": access_token.jwt,
            },
            status=status.HTTP_200_OK,
        )
