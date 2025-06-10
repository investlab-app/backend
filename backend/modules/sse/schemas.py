import uuid

from pydantic import BaseModel, Field

from modules.sse.serializers import SSERequestSerializer


class SSERequestParams(BaseModel):
    symbols: set[str]
    connection_id: uuid.UUID = Field(..., alias="connectionId")

    class ConfigDict:
        populate_by_name = True

    @staticmethod
    def parse(data: dict) -> "SSERequestParams":
        serializer = SSERequestSerializer(data=data)

        if not serializer.is_valid():
            raise ValueError(f"Invalid SSE request data: {serializer.errors}")

        validated_data = serializer.validated_data.copy()
        validated_data["symbols"] = set(validated_data["symbols"])
        return SSERequestParams.model_validate(validated_data)
