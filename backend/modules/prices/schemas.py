import uuid
from collections.abc import Callable

from pydantic import BaseModel




type HandlerFn = Callable[[dict[str, float]], None]
type ClientId = uuid.UUID
type TickerId = str


class Client(BaseModel):
    tickers: set[TickerId]
    handler: HandlerFn | None = None

    @staticmethod
    def empty() -> "Client":
        return Client(tickers=set(), handler=None)
