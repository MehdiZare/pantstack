from services.web.domain.models.request import ScheduleRequest
from services.web.domain.ports.jobs import JobRepository, QueuePort


class JobService:
    """Service for job management."""

    def __init__(self, job_repo: JobRepository, queue: QueuePort):
        self.job_repo = job_repo
        self.queue = queue

    def schedule_job(self, req: ScheduleRequest) -> dict[str, str]:
        """Schedule a new job."""
        cid = self.queue.publish(req.job_type, req.params)
        return {"id": cid}

    def get_job_status(self, correlation_id: str) -> dict | None:
        """Get job status by correlation ID."""
        return self.job_repo.get_status(correlation_id)

    def cancel_job(self, correlation_id: str) -> None:
        """Cancel a job."""
        self.job_repo.mark_canceled(correlation_id)
