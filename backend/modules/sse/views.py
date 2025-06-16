from dependency_injector.wiring import Provide, inject
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from config.containers import AppContainer
from config.logging import get_logger
from modules.prices.services import LivePrices
from modules.sse.schemas import SSERequestParams
from modules.sse.serializers import SSERequestSerializer

logger = get_logger(__name__)


class SSESubscribeView(APIView):
    @inject
    def __init__(
        self,
        live_prices: LivePrices = Provide[AppContainer.prices_container.live_prices],
    ):
        super().__init__()
        self.live_prices = live_prices

    @extend_schema(request=SSERequestSerializer)
    def put(self, request):
        try:
            params = SSERequestParams.parse(request.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        connection_id = params.connection_id
        symbols = params.symbols

        try:
            self.live_prices.subscribe(connection_id, symbols)
            logger.debug("%s: Subscribed to symbols: %s", connection_id, symbols)
            return Response(
                {"message": f"Subscribed to new events: {symbols}"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(
                "%s: Failed to subscribe to symbols %s: %s",
                connection_id,
                symbols,
                str(e),
            )
            return Response(
                {"error": f"Failed to subscribe to symbols: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class SSEUnsubscribeView(APIView):
    @inject
    def __init__(
        self,
        live_prices: LivePrices = Provide[AppContainer.prices_container.live_prices],
    ):
        super().__init__()
        self.live_prices = live_prices

    @extend_schema(request=SSERequestSerializer)
    def put(self, request):
        try:
            params = SSERequestParams.parse(request.data)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        connection_id = params.connection_id
        symbols = params.symbols

        try:
            self.live_prices.unsubscribe(connection_id, symbols)
            logger.debug("%s: Unsubscribed from symbols: %s", connection_id, symbols)
            return Response(
                {"message": f"Unsubscribed from events: {symbols}"},
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            logger.error(
                "%s: Failed to unsubscribe from symbols %s: %s",
                connection_id,
                symbols,
                str(e),
            )
            return Response(
                {"error": f"Failed to unsubscribe from symbols: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
