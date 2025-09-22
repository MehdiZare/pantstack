"""Celery worker configuration."""

from typing import Any, Dict

from pydantic import Field

from shared.core.config import CeleryConfig


class CeleryWorkerConfig(CeleryConfig):
    """Extended Celery configuration for the worker."""

    worker_name: str = Field(default="pantstack-worker", description="Worker name")
    worker_concurrency: int = Field(
        default=4, description="Number of concurrent workers"
    )
    worker_loglevel: str = Field(default="info", description="Log level")
    worker_send_events: bool = Field(default=True, description="Send worker events")
    worker_pool: str = Field(default="prefork", description="Worker pool type")

    # Beat scheduler settings (for periodic tasks)
    beat_schedule_filename: str = Field(
        default="celerybeat-schedule", description="Beat schedule database file"
    )
    beat_max_loop_interval: int = Field(
        default=300, description="Maximum seconds to sleep between beat iterations"
    )

    @classmethod
    def from_environment(cls) -> "CeleryWorkerConfig":
        """Load configuration from environment."""
        # CeleryConfig doesn't have from_environment, so create directly
        config = cls()
        config.worker_name = "pantstack-worker"

        # Auto-configure task routing for discovered services
        # This will be populated by the registry
        config.task_routes = {}

        return config

    def to_celery_config(self) -> Dict[str, Any]:
        """Convert to Celery configuration format.

        Returns:
            Dictionary with Celery settings
        """
        return {
            # Broker settings
            "broker_url": self.broker_url,
            "result_backend": self.result_backend,
            # Serialization
            "task_serializer": self.task_serializer,
            "result_serializer": self.result_serializer,
            "accept_content": self.accept_content,
            # Time settings
            "timezone": self.timezone,
            "enable_utc": self.enable_utc,
            # Task settings
            "task_track_started": self.task_track_started,
            "task_time_limit": self.task_time_limit,
            "task_soft_time_limit": self.task_soft_time_limit,
            # Worker settings
            "worker_prefetch_multiplier": self.worker_prefetch_multiplier,
            "worker_max_tasks_per_child": self.worker_max_tasks_per_child,
            "worker_send_task_events": self.worker_send_events,
            # Routing
            "task_routes": self.task_routes,
            "task_default_queue": self.task_default_queue,
            # Result settings
            "result_expires": 3600,  # Results expire after 1 hour
            "result_compression": "gzip",
            # Security
            "worker_hijack_root_logger": False,
            "worker_log_color": False,
        }
