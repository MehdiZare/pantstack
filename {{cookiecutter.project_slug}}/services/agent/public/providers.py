from services.agent.adapters.repositories.s3_jobs import S3JobRepository


def provide_job_repo() -> S3JobRepository:
    return S3JobRepository.from_env()
