"""Run script for Celery worker."""

import os
import sys


def main():
    """Run the Celery worker."""
    from celery import current_app
    from celery.bin import worker

    from .app import app

    # Worker configuration
    loglevel = os.getenv("CELERY_LOGLEVEL", "info")
    concurrency = int(os.getenv("CELERY_CONCURRENCY", "4"))
    queues = os.getenv("CELERY_QUEUES", "").split(",") if os.getenv("CELERY_QUEUES") else None
    pool = os.getenv("CELERY_POOL", "prefork")

    # Create worker
    celery_worker = worker.worker(app=app)

    # Worker options
    options = {
        "loglevel": loglevel,
        "concurrency": concurrency,
        "pool": pool,
        "hostname": os.getenv("CELERY_HOSTNAME", "worker@%h"),
    }

    if queues:
        options["queues"] = queues

    # Start worker
    celery_worker.run(**options)


if __name__ == "__main__":
    main()