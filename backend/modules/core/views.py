from rest_framework.generics import GenericAPIView
from rest_framework.response import Response


class HealthCheckView(GenericAPIView):
    permission_classes = []
    serializer_class = None

    def get(self, _):
        return Response({"message": "App is running!"})
