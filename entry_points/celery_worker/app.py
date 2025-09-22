"""Celery application with auto-discovery."""

from celery import Celery
from celery.signals import worker_ready

from shared.utils import setup_logging

from .config import CeleryWorkerConfig
from .registry import CeleryRegistry


def create_celery_app() -> Celery:
    """Create and configure Celery application.

    Returns:
        Configured Celery application
    """
    # Load configuration
    config = CeleryWorkerConfig.from_environment()
    setup_logging(config)

    # Create Celery app
    app = Celery(config.worker_name)

    # Apply configuration
    app.config_from_object(config.to_celery_config())

    # Discover and register tasks from all services
    print("\n📦 Discovering Celery tasks from services...")
    registry = CeleryRegistry(app)
    manifests = registry.discover_services()

    # Store registry in app for access
    app.registry = registry

    print(f"\n✅ Celery worker configured")
    print(f"  - Services: {len(manifests)}")
    print(f"  - Broker: {config.broker_url}")
    print(f"  - Backend: {config.result_backend}")

    # Log discovered tasks by service
    tasks_by_service = registry.get_all_tasks()
    if tasks_by_service:
        print("\n📋 Discovered tasks:")
        for service, tasks in tasks_by_service.items():
            print(f"  {service}:")
            for task in tasks:
                print(f"    - {task}")

    return app


# Create the Celery app instance
app = create_celery_app()


@worker_ready.connect
def worker_ready_handler(sender=None, **kwargs):
    """Handler for when worker is ready."""
    print("\n🚀 Celery worker is ready and accepting tasks!")
    print(f"  - Hostname: {sender.hostname if sender else 'unknown'}")
    print(f"  - Queues: {', '.join(q.name for q in app.conf.task_queues)}")


# Beat schedule for periodic tasks
app.conf.beat_schedule = {
    # Example periodic tasks
    "cleanup-inactive-users": {
        "task": "auth.cleanup_inactive_users",
        "schedule": 86400.0,  # Daily
        "options": {"queue": "auth"},
    },
    "health-check": {
        "task": "system.health_check",
        "schedule": 60.0,  # Every minute
        "options": {"queue": "default"},
    },
}
