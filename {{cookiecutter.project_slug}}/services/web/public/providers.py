import os

from services.web.adapters.eventbridge_publisher import EventBridgePublisher
from services.web.adapters.repositories.s3_jobs import S3JobRepository
from services.web.adapters.repositories.sqs_queue import SqsQueue


def provide_queue():
    bus = os.getenv("EVENT_BUS_NAME")
    if bus and os.getenv("LOCALSTACK", "").lower() not in ("1", "true", "yes", "on"):
        return EventBridgePublisher.from_env()
    return SqsQueue.from_env()


def provide_job_repo() -> S3JobRepository:
    return S3JobRepository.from_env()
