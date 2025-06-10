import logging
from typing import cast

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response

from modules.instruments.exceptions import FetchInstrumentInfoException, FetchInstrumentNewsException
from modules.instruments.serializers import (
    InstrumentDetailedInfoSerializer,
    InstrumentInfoSerializer,
    InstrumentsListQueryParams,
    PaginatedInstrumentsResponseSerializer,
)
from modules.instruments.services import InstrumentsServiceMinimal


class InstrumentsAvailableView(generics.GenericAPIView):
    @extend_schema(
        responses=[PaginatedInstrumentsResponseSerializer],
    )
    def get(self, request: Request) -> Response:
        """
        Get a list of some available instruments (from S&P 500 for 6/9/2025).
        """
        service = InstrumentsServiceMinimal()

        instruments: list[str] = service.get_instruments_available()

        return Response(data={"instruments": instruments}, status=status.HTTP_200_OK)


class InstrumentsListView(generics.GenericAPIView):
    @extend_schema(
        parameters=[InstrumentsListQueryParams],
        responses=[PaginatedInstrumentsResponseSerializer],
        request=InstrumentsListQueryParams,
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

        validated = cast(dict, params.validated_data)  # pylint: disable=duplicate-code

        tickers = list(
            {
                t.upper()
                for t in (piece.strip() for piece in validated["tickers"].split(","))
                if t
            }
        )
        service = InstrumentsServiceMinimal()

        try:
            result = service.get_instruments_list(
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
    @extend_schema(
        responses=[InstrumentDetailedInfoSerializer],
    )
    def get(
            self, request: Request, ticker: str
    ) -> Response:  # pylint: disable=unused-argument
        """
        Get detailed information for a single instrument.
        """
        service = InstrumentsServiceMinimal()

        try:
            result = service.get_instrument_detailed_info(ticker)
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
    def get(self, request: Request, ticker: str) -> Response:
        """

        Args:
            request (Request): The HTTP request object.
            ticker (str): The ticker symbol to fetch news for.

        Returns:
            Response: A response containing the news items for the instrument.
        """
        service = InstrumentsServiceMinimal()

        try:
            result = service.get_news(ticker)
        except FetchInstrumentNewsException as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        result_dict = [item.model_dump() for item in result]

        return Response(result_dict)
