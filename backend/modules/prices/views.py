from typing import cast

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.request import Request
from rest_framework.response import Response

from modules.prices.exceptions import FetchPriceException, InvalidTimeIntervalException
from modules.prices.serializers import (
    InstrumentPriceQueryParams,
    InstrumentPriceResponseSerializer,
)
from modules.prices.services import PricesServiceMinimal


class PricesView(generics.GenericAPIView):

    @extend_schema(
        parameters=[InstrumentPriceQueryParams],
        responses=[InstrumentPriceResponseSerializer(many=True)],
        request=InstrumentPriceQueryParams,
    )
    def get(self, request: Request) -> Response:
        params = InstrumentPriceQueryParams(data=request.query_params)
        if not params.is_valid():
            return Response(
                {"errors": params.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        validated = cast(dict, params.validated_data)

        try:
            service = PricesServiceMinimal()
            price_history = service.get_instrument_price_history(
                validated["ticker"],
                validated["start_date"],
                validated["end_date"],
                validated["interval"],
            )
        except (FetchPriceException, InvalidTimeIntervalException) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        records = [
            InstrumentPriceResponseSerializer.sanitize_output(item.model_dump())
            for item in price_history["data"]
        ]
        serialized = InstrumentPriceResponseSerializer(data=records, many=True)

        if not serialized.is_valid():
            return Response(
                {"errors": serialized.errors},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            {
                "data": serialized.data,
                "min_price": price_history["min_price"],
                "max_price": price_history["max_price"],
            }
        )
