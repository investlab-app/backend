from typing import cast

from dependency_injector.wiring import Provide, inject
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response

from config.containers import AppContainer
from config.logging import get_logger
from modules.instruments.exceptions import (
    FetchInstrumentInfoException,
    FetchInstrumentNewsException,
)
from modules.instruments.serializers import (
    InstrumentDetailedInfoSerializer,
    InstrumentInfoSerializer,
    InstrumentsListQueryParams,
    PaginatedInstrumentsResponseSerializer,
    InstrumentV2InfoSerializer
)
from modules.instruments.services import InstrumentsService, InstrumentServiceV2

logger = get_logger(__name__)


class InstrumentsAvailableView(generics.GenericAPIView):
    @inject
    def __init__(
        self,
        service: InstrumentsService = Provide[
            AppContainer.instruments_container.instruments_service
        ],
    ):
        super().__init__()
        self.service = service

    @extend_schema(
        responses={
            "200": {
                "type": "object",
                "properties": {
                    "instruments": {"type": "array", "items": {"type": "string"}}
                },
            }
        },
    )
    def get(self, request: Request) -> Response:
        """
        Get a list of some available instruments (from S&P 500 for 6/9/2025).
        """
        logger.debug("Getting available instruments from service: %s", self.service)
        instruments: list[str] = self.service.get_instruments_available()
        logger.debug("Got instruments: %s", instruments)

        return Response(data={"instruments": instruments}, status=status.HTTP_200_OK)


class InstrumentsListView(generics.GenericAPIView):
    @inject
    def __init__(
        self,
        service: InstrumentsService = Provide[
            AppContainer.instruments_container.instruments_service
        ],
    ):
        super().__init__()
        self.service = service

    @extend_schema(
        parameters=[InstrumentsListQueryParams],
        responses={200: PaginatedInstrumentsResponseSerializer},
        summary="List instruments with pagination",
        description="Get a paginated list of financial instruments",
        operation_id="instruments_list",
    )
    def get(self, request: Request) -> Response:
        """
        Get a paginated, sorted, and filtered list of instruments.
        """
        params = InstrumentsListQueryParams(data=request.query_params)
        if not params.is_valid():
            return Response(
                {"errors": params.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        validated = cast("dict", params.validated_data)  # pylint: disable=duplicate-code

        raw_tickers = (validated.get("tickers") or "").split(",")
        tickers = list(
            {t.upper() for t in (piece.strip() for piece in raw_tickers) if t}
        )

        try:
            result = self.service.get_instruments_list(
                tickers=tickers,
                page=validated.get("page", 1),
                page_size=validated.get("page_size", 10),
                sort_by=validated.get("sort_by"),
                sort_direction=validated.get("sort_direction", "asc"),
                filter_sector=validated.get("sector"),
                filter_industry=validated.get("industry"),
            )
        except FetchInstrumentInfoException as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        processed_items = [
            InstrumentInfoSerializer.sanitize_output(item.model_dump())
            for item in result["items"]
        ]

        response_data = {
            "items": processed_items,
            "total": result["total"],
            "page": result["page"],
            "page_size": result["page_size"],
            "num_pages": result["num_pages"],
        }

        serialized = PaginatedInstrumentsResponseSerializer(data=response_data)

        if not serialized.is_valid():
            return Response(
                {"errors": serialized.errors},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(serialized.data)


class InstrumentDetailView(generics.GenericAPIView):
    def __init__(
        self,
        service: InstrumentsService = Provide[
            AppContainer.instruments_container.instruments_service
        ],
    ):
        super().__init__()
        self._service = service

    @extend_schema(
        responses={200: InstrumentDetailedInfoSerializer},
        summary="Get instrument details",
        description="Get detailed information about a specific instrument by ticker",
        operation_id="instrument_detail",
    )
    def get(self, request: Request, ticker: str) -> Response:  # pylint: disable=unused-argument
        """
        Get detailed information for a single instrument.
        """
        try:
            result = self._service.get_instrument_detailed_info(ticker)
        except FetchInstrumentInfoException as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        result_dict = result.model_dump()

        processed_data = InstrumentDetailedInfoSerializer.sanitize_output(result_dict)

        serialized = InstrumentDetailedInfoSerializer(data=processed_data)

        if not serialized.is_valid():
            return Response(
                {"errors": serialized.errors},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(serialized.data)


class InstrumentNewsView(generics.GenericAPIView):
    @inject
    def __init__(
        self,
        service: InstrumentsService = Provide[
            AppContainer.instruments_container.instruments_service
        ],
    ):
        super().__init__()
        self.service = service

    @extend_schema(
        responses={
            "200": {
                "type": "array",
                "items": {
                    "type": "object",
                    "description": "News item for the instrument",
                },
            }
        },
    )
    def get(self, request: Request, ticker: str) -> Response:
        """

        Args:
            request (Request): The HTTP request object.
            ticker (str): The ticker symbol to fetch news for.

        Returns:
            Response: A response containing the news items for the instrument.
        """
        try:
            result = self.service.get_news(ticker)
        except FetchInstrumentNewsException as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        result_dict = [item.model_dump() for item in result]

        return Response(result_dict)

class InstrumentPullView(generics.GenericAPIView):
    serializer_class = InstrumentV2InfoSerializer
    queryset = None

    def get(self, request: Request) -> Response:
        InstrumentServiceV2.pull_all_instruments()
        return Response("done")
