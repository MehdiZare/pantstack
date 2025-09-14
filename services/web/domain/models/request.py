from pydantic import BaseModel


class ScheduleRequest(BaseModel):
    job_type: str
    params: dict
