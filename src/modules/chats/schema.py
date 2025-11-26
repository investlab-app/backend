from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class ChatMessageSchema(BaseModel):
    id: str = ""
    role: Literal["user", "assistant"] = "user"
    content: str = ""
    createdAt: datetime | None = None  # noqa: N815
