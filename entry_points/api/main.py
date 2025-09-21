"""Main FastAPI application with automatic service discovery."""

import os
from typing import Any, Dict

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from shared.core.config import BaseConfig
from shared.core.registry import SecurityGroup
from shared.core.security import (
    admin_endpoint,
    authenticated_endpoint,
    internal_endpoint,
    public_endpoint,
)
from shared.utils import get_config, set_config, setup_logging

from .registry import APIRegistry


def create_app() -> FastAPI:
    """Create FastAPI application with discovered routes.

    Returns:
        Configured FastAPI application
    """
    # Load configuration
    config = BaseConfig.from_environment()
    set_config(config)
    setup_logging(config)

    # Create FastAPI app
    app = FastAPI(
        title="Pantstack API",
        description="Aggregated API from all services",
        version="1.0.0",
        debug=config.debug,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Store configuration in app state
    app.state.config = config

    # Discover and register all service routes
    print("\n📦 Discovering services and routes...")
    registry = APIRegistry()
    manifests = registry.discover_services()

    # Store registry in app state
    app.state.registry = registry

    # Register routers with appropriate security
    # Public routes (no auth)
    public_router = registry.get_router_for_group(SecurityGroup.PUBLIC)
    app.include_router(public_router)

    # Authenticated routes
    auth_router = registry.get_router_for_group(SecurityGroup.AUTHENTICATED)
    auth_router.dependencies.append(Depends(authenticated_endpoint))
    app.include_router(auth_router)

    # Admin routes
    admin_router = registry.get_router_for_group(SecurityGroup.ADMIN)
    admin_router.dependencies.append(Depends(admin_endpoint))
    app.include_router(admin_router)

    # Internal routes (service-to-service)
    internal_router = registry.get_router_for_group(SecurityGroup.INTERNAL)
    internal_router.dependencies.append(Depends(internal_endpoint))
    app.include_router(internal_router)

    # Add root endpoints
    @app.get("/", tags=["root"])
    async def root() -> Dict[str, Any]:
        """Root endpoint."""
        return {
            "name": config.app_name,
            "version": "1.0.0",
            "environment": config.environment,
            "services": len(manifests),
        }

    @app.get("/health", tags=["monitoring"])
    async def health_check() -> Dict[str, Any]:
        """Health check endpoint."""
        return {
            "status": "healthy",
            "environment": config.environment,
            "services": [m.service_name for m in manifests],
            "routes_loaded": sum(len(m.routes) for m in manifests),
        }

    @app.get("/api/services", tags=["discovery"])
    async def list_services() -> Dict[str, Any]:
        """List all discovered services."""
        return {
            "services": [
                {
                    "name": m.service_name,
                    "version": m.version,
                    "routes": len(m.routes),
                    "tasks": len(m.tasks),
                    "handlers": len(m.handlers),
                }
                for m in manifests
            ]
        }

    @app.get("/api/routes", tags=["discovery"])
    async def list_routes() -> Dict[str, Any]:
        """List all registered routes grouped by security."""
        return registry.get_all_routes()

    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Application startup event."""
        print("\n🚀 Pantstack API started")
        print(f"📊 Environment: {config.environment}")
        print(f"🔧 Debug: {config.debug}")
        print(f"📦 Services: {len(manifests)}")
        print(f"🛣️ Total routes: {sum(len(m.routes) for m in manifests)}")

        if config.debug:
            print("\n📋 Registered services:")
            for manifest in manifests:
                print(f"  - {manifest.service_name} v{manifest.version}")
                if manifest.routes:
                    print(f"    Routes: {len(manifest.routes)}")
                if manifest.tasks:
                    print(f"    Tasks: {len(manifest.tasks)}")
                if manifest.handlers:
                    print(f"    Handlers: {len(manifest.handlers)}")

    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Application shutdown event."""
        print("\n👋 Pantstack API shutting down")

    # Exception handler for better error responses
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """Global exception handler."""
        import traceback

        if config.debug:
            return JSONResponse(
                status_code=500,
                content={
                    "error": str(exc),
                    "type": type(exc).__name__,
                    "traceback": traceback.format_exc().split("\n"),
                },
            )
        else:
            return JSONResponse(
                status_code=500, content={"error": "Internal server error"}
            )

    return app


# Create app instance for uvicorn
app = create_app()