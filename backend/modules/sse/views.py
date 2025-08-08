from dependency_injector.wiring import Provide, inject
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from config.containers import AppContainer
from config.logging import get_logger
from modules.sse.schemas import SSERequestParams
from modules.sse.serializers import SSERequestSerializer
from modules.sse.services import SSEService

logger = get_logger(__name__)


class SSEUpdateView(APIView):
    @inject
    def __init__(
        self,
        sse_service: SSEService = Provide[AppContainer.prices_container.sse_service],
    ):
        super().__init__()
        self._sse_service = sse_service

    @extend_schema(request=SSERequestSerializer)
    def put(self, request):
        try:
            params = SSERequestParams.parse(request.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        logger.debug("Received SSE update request: %s", params)

        connection_id = params.connection_id
        events = params.events

        try:
            self._sse_service.update(connection_id, events)
            logger.debug("%s: Updated events: %s", connection_id, events)
            return Response(
                {"message": f"Updated events: {events}"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(
                "%s: Failed to update events %s: %s",
                connection_id,
                events,
                str(e),
            )
            return Response(
                {"error": f"Failed to update events: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
