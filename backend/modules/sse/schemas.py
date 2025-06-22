import uuid

from pydantic import BaseModel

from modules.sse.serializers import SSERequestSerializer


class SSERequestParams(BaseModel):
    symbols: set[str]
    connection_id: uuid.UUID

    class ConfigDict:
        from_attributes = True

    @staticmethod
    def parse(data: dict) -> "SSERequestParams":
        serializer = SSERequestSerializer(data=data)

        if not serializer.is_valid():
            raise ValueError(f"Invalid SSE request data: {serializer.errors}")

        return SSERequestParams.model_validate(serializer.validated_data)
