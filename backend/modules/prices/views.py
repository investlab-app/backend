from typing import cast

from drf_spectacular.utils import extend_schema
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from modules.prices.errors import (
    FetchPriceException,
    IllegalDateOrderException,
    InvalidTimeIntervalException,
)
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
        try:
            params = InstrumentPriceQueryParams(data=request.query_params)
            params.is_valid(raise_exception=True)
            validated = cast(dict, params.validated_data)
            service = PricesServiceMinimal()
            instrument_data = service.get_instrument_price_for_timeperiod(
                validated["ticker"],
                validated["start_date"],
                validated["end_date"],
                validated["interval"],
            )
            records = [
                InstrumentPriceResponseSerializer.sanitize_output(item.model_dump())
                for item in instrument_data
            ]
            serialized = InstrumentPriceResponseSerializer(data=records, many=True)

            if not serialized.is_valid():
                print(serialized.errors)
                return Response(
                    {"errors": serialized.errors},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            return Response(serialized.data)

        except FetchPriceException as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        except IllegalDateOrderException as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except InvalidTimeIntervalException as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except ValidationError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Exception as e:
            return Response(
                {"detail": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
