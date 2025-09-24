"""Auth service API with module discovery.

Example of how to use module discovery in a service API.
"""

from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from shared.core.config import BaseConfig
from shared.core.module_discovery import ModuleDiscovery
from shared.utils import set_config, setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Initialize modules on startup
    discovery: ModuleDiscovery = app.state.discovery
    discovery.discover_modules()
    discovery.initialize_all()

    yield

    # Cleanup modules on shutdown
    discovery.shutdown_all()


def create_app() -> FastAPI:
    """Create FastAPI application with module discovery.

    Returns:
        Configured FastAPI application with discovered modules
    """
    # Load configuration
    config = BaseConfig.from_environment()
    set_config(config)
    setup_logging(config)

    # Create FastAPI app
    app = FastAPI(
        title="Auth Service API",
        description="Authentication service with modular architecture",
        version="1.0.0",
        debug=config.debug,
        lifespan=lifespan,
    )

    # Initialize module discovery
    discovery = ModuleDiscovery("auth")
    app.state.discovery = discovery

    # Discover and register module routes
    discovery.discover_modules()
    for router in discovery.get_all_routes():
        app.include_router(router, prefix="/api/v1")

    # Add service info endpoint
    @app.get("/")
    async def service_info():
        """Get service information."""
        modules = discovery.list_modules()
        return {
            "service": "auth",
            "version": "1.0.0",
            "modules": modules,
            "module_count": len(modules),
            "status": "healthy",
        }

    # Add module info endpoint
    @app.get("/modules")
    async def list_modules():
        """List all loaded modules."""
        modules_info = []
        for name, module in discovery.modules.items():
            modules_info.append(
                {
                    "name": name,
                    "has_routes": module.get_routes() is not None,
                    "task_count": len(module.get_tasks() or []),
                    "handler_count": len(module.get_handlers() or {}),
                }
            )
        return {"modules": modules_info}

    # Add module-specific info endpoint
    @app.get("/modules/{module_name}")
    async def get_module_info(module_name: str):
        """Get information about a specific module."""
        module = discovery.get_module(module_name)
        if not module:
            raise HTTPException(
                status_code=404,
                detail=f"Module '{module_name}' not found",
            )

        return {
            "name": module.name,
            "routes": module.get_routes() is not None,
            "tasks": module.get_tasks() or [],
            "handlers": (
                list(module.get_handlers().keys()) if module.get_handlers() else []
            ),
        }

    # Add health check
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        # Check if all modules are initialized
        module_status = {}
        for name, module in discovery.modules.items():
            try:
                # Try to get module info as a basic health check
                module.get_routes()
                module_status[name] = "healthy"
            except Exception as e:
                module_status[name] = f"unhealthy: {str(e)}"

        all_healthy = all(status == "healthy" for status in module_status.values())

        return {
            "status": "healthy" if all_healthy else "degraded",
            "modules": module_status,
        }

    return app


# Example for Lambda entry point with selective loading
def create_lambda_handler():
    """Create Lambda handler with selective module loading.

    This demonstrates how to create a lightweight Lambda function
    that only loads specific modules.
    """
    from shared.core.module_discovery import SelectiveModuleLoader

    loader = SelectiveModuleLoader("auth")

    # Only load the modules needed for token validation
    modules = loader.load_for_lambda(["tokens", "validation"])

    def handler(event, context):
        """Lambda handler function."""
        token_module = modules.get("tokens")
        if not token_module:
            return {
                "statusCode": 500,
                "body": "Token module not available",
            }

        # Use the module to validate token
        # result = token_module.validate(event.get("token"))

        return {
            "statusCode": 200,
            "body": "Token validated",
        }

    return handler


# Example for Worker entry point
def create_worker_app():
    """Create Celery worker with module tasks.

    This demonstrates how to create a worker that only loads
    modules with background tasks.
    """
    from celery import Celery

    from shared.core.module_discovery import SelectiveModuleLoader

    # Create Celery app
    celery_app = Celery("auth_worker")

    # Load only modules with tasks
    loader = SelectiveModuleLoader("auth")
    modules = loader.load_for_worker()

    # Register all module tasks
    all_tasks = []
    for module in modules.values():
        tasks = module.get_tasks()
        if tasks:
            all_tasks.extend(tasks)

    # Configure Celery with discovered tasks
    celery_app.conf.update(
        task_routes={task: {"queue": "auth"} for task in all_tasks},
        task_annotations={task: {"rate_limit": "10/s"} for task in all_tasks},
    )

    return celery_app


if __name__ == "__main__":
    import uvicorn

    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8000)
