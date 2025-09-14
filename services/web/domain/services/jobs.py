from services.web.domain.models.request import ScheduleRequest
from services.web.domain.ports.jobs import JobRepository, QueuePort


def schedule_job(queue: QueuePort, req: ScheduleRequest) -> dict[str, str]:
    cid = queue.publish(req.job_type, req.params)
    return {"id": cid}


def get_job_status(repo: JobRepository, correlation_id: str) -> dict | None:
    return repo.get_status(correlation_id)


def cancel_job(repo: JobRepository, correlation_id: str) -> None:
    repo.mark_canceled(correlation_id)
