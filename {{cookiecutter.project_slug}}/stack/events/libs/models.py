from datetime import datetime

from pydantic import BaseModel  # pants: no-infer-dep


class EventEnvelope(BaseModel):
    type: str
    version: int
    id: str
    at: datetime
    correlation_id: str | None = None
    data: dict


# Common job event contracts
class JobRequested(BaseModel):
    job_type: str
    params: dict
    requested_by: str | None = None


class JobProgress(BaseModel):
    id: str
    progress: int
    message: str | None = None


class JobCompleted(BaseModel):
    id: str
    status: str
    result: dict | None = None
