import logging  # Add logger import

from django.conf import settings  # Add settings import
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from clerk_backend_api import (
    Clerk,
    CreateSessionRequestBodyTypedDict,
    GetUserListRequestTypedDict,
)

from modules.authentication.serializers import ClerkLoginSerializer

logger = logging.getLogger(__name__)  # Initialize logger


@method_decorator(csrf_exempt, name="dispatch")
class ClerkUsernamePasswordSignInView(APIView):
    """
    Handles Clerk authentication via username (email) and password.
    Returns a Clerk sign-in token upon successful authentication.
    """

    authentication_classes = []  # Explicitly set
    permission_classes = [AllowAny]  # Explicitly set
    serializer_class = ClerkLoginSerializer  # Added for Swagger

    @extend_schema(
        request=ClerkLoginSerializer,
        responses={
            200: OpenApiResponse(description="Sign-in successful, token returned."),
            400: OpenApiResponse(description="Invalid credentials or user not found."),
            401: OpenApiResponse(description="Password verification failed."),
            500: OpenApiResponse(
                description="Clerk SDK error or other internal server error."
            ),
        },
        summary="Sign in a user with email and password via Clerk",
        description="Authenticates a user using their email and password through Clerk, returning a sign-in token upon success.",
    )
    def post(self, request, *args, **kwargs):
        """
        Sign in a user with email and password via Clerk.
        """
        print(f"Request data: {request.data}")  # Debugging line

        serializer = self.serializer_class(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data["email"]

        password = serializer.validated_data["password"]

        clerk_sdk = Clerk(settings.CLERK_SECRET_KEY)

        # res = clerk_sdk.users.create(
        #     request=CreateUserRequestBodyTypedDict(
        #         first_name="Twoj",
        #         last_name="Stary",
        #         email_address=[email],
        #         password=password,
        #     )
        # )
        # print(res)

        users = clerk_sdk.users.list(
            request=GetUserListRequestTypedDict(email_address=[email])
        )
        # print(users)

        our_user = users[0]

        verify_response = clerk_sdk.users.verify_password(
            user_id=our_user.id, password=password
        )
        print(f"Verify response: {verify_response}")

        session = clerk_sdk.sessions.create(
            request=CreateSessionRequestBodyTypedDict(user_id=our_user.id)
        )
        print(f"Session created: {session}")

        session_id = session.id
        print(f"Session ID: {session_id}")

        jwt_token = clerk_sdk.sessions.create_token(session_id=session_id)
        print(f"JWT Token: {jwt_token}")

        return Response(
            {
                "message": "Sign-in successful",
                "session_id": session_id,
                "token": jwt_token,
            },
            status=status.HTTP_200_OK,
        )
