"""Agent service public API."""

from shared.core.registry import SecurityGroup, ServiceManifest, ServiceRoute

# Import the FastAPI app to register routes
try:
    from ..app.api.main import app

    # Extract routes from the FastAPI app
    routes = []
    for route in app.routes:
        if hasattr(route, "path") and hasattr(route, "methods"):
            for method in route.methods:
                routes.append(
                    ServiceRoute(
                        path=f"/agent{route.path}",
                        method=method,
                        handler=route.endpoint,
                        security_group=SecurityGroup.PUBLIC,
                    )
                )

    # Create service manifest
    SERVICE_MANIFEST = ServiceManifest(
        service_name="agent",
        version="1.0.0",
        routes=routes,
        tasks=[
            "agent.process_data",
            "agent.execute_workflow",
            "agent.generate_report",
            "agent.batch_process",
            "agent.sync_external_data",
            "agent.health_check",
            "agent.cleanup_old_data",
            "agent.send_notification",
        ],
        handlers=[],
    )
except ImportError:
    # Fallback manifest if app can't be imported
    SERVICE_MANIFEST = ServiceManifest(
        service_name="agent",
        version="1.0.0",
        routes=[
            ServiceRoute(
                path="/agent/tasks",
                method="POST",
                handler=None,
                security_group=SecurityGroup.PUBLIC,
            ),
            ServiceRoute(
                path="/agent/tasks/{task_id}",
                method="GET",
                handler=None,
                security_group=SecurityGroup.PUBLIC,
            ),
            ServiceRoute(
                path="/agent/health",
                method="GET",
                handler=None,
                security_group=SecurityGroup.PUBLIC,
            ),
        ],
        tasks=[
            "agent.process_data",
            "agent.execute_workflow",
            "agent.generate_report",
        ],
        handlers=[],
    )

__all__ = ["SERVICE_MANIFEST"]
