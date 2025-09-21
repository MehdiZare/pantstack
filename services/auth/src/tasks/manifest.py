"""Task manifest for auth service Celery task discovery."""

from shared.core.registry import ServiceManifest

# Create service manifest with task modules
manifest = ServiceManifest(
    service_name="auth",
    version="1.0.0",
    description="Authentication service Celery tasks",
    task_modules=[
        "user_tasks",
        "email_tasks",
        "event_tasks",
    ],
    # Task routing will use service name as queue
)