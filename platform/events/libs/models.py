from datetime import datetime

from pydantic import BaseModel


class EventEnvelope(BaseModel):
    type: str
    version: int
    id: str
    at: datetime
    correlation_id: str | None = None
    data: dict
