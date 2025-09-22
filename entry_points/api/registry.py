"""API registry for discovering and aggregating routes from all services."""

from typing import Dict, List

from fastapi import APIRouter, Depends

from shared.core.discovery import AutoDiscovery
from shared.core.registry import SecurityGroup, ServiceManifest, ServiceRegistry


class APIRegistry(ServiceRegistry):
    """Registry for API routes from all services."""

    def __init__(self):
        super().__init__()
        self.routers: Dict[SecurityGroup, APIRouter] = self._create_routers()

    def _create_routers(self) -> Dict[SecurityGroup, APIRouter]:
        """Create routers for each security group.

        Returns:
            Dictionary of security group to router mapping
        """
        return {
            SecurityGroup.PUBLIC: APIRouter(
                prefix="/api/v1/public",
                tags=["public"],
            ),
            SecurityGroup.AUTHENTICATED: APIRouter(
                prefix="/api/v1",
                tags=["authenticated"],
            ),
            SecurityGroup.ADMIN: APIRouter(
                prefix="/api/v1/admin",
                tags=["admin"],
            ),
            SecurityGroup.INTERNAL: APIRouter(
                prefix="/api/v1/internal",
                tags=["internal"],
            ),
        }

    def discover_services(self) -> List[ServiceManifest]:
        """Discover all services with API routes.

        Returns:
            List of service manifests
        """
        services = AutoDiscovery.discover_services()

        for service_name in services:
            manifest = AutoDiscovery.load_service_manifest(service_name, "api")
            if manifest:
                self.register(manifest)
                self._register_routes(manifest)

        # Validate dependencies
        errors = self.validate_dependencies()
        if errors:
            for error in errors:
                print(f"⚠️ Dependency warning: {error}")

        return self.get_all_manifests()

    def _register_routes(self, manifest: ServiceManifest) -> None:
        """Register routes from a service manifest.

        Args:
            manifest: Service manifest containing routes
        """
        for route_def in manifest.routes:
            router = self.routers.get(route_def.security_group)
            if not router:
                print(
                    f"⚠️ Unknown security group {route_def.security_group} for route {route_def.path}"
                )
                continue

            # Create full path with service prefix
            full_path = f"/{manifest.service_name}{route_def.path}"

            # Add route to appropriate router
            try:
                router.add_api_route(
                    path=full_path,
                    endpoint=route_def.handler,
                    methods=[route_def.method],
                    tags=route_def.tags or [manifest.service_name],
                    description=route_def.description,
                    dependencies=route_def.dependencies,
                )
                print(
                    f"  ✅ Registered route: {route_def.method} {full_path} [{route_def.security_group.value}]"
                )
            except Exception as e:
                print(f"  ❌ Failed to register route {full_path}: {e}")

    def get_router_for_group(self, security_group: SecurityGroup) -> APIRouter:
        """Get router for a specific security group.

        Args:
            security_group: Security group

        Returns:
            FastAPI router
        """
        return self.routers[security_group]

    def get_all_routes(self) -> Dict[str, List[str]]:
        """Get all registered routes grouped by security.

        Returns:
            Dictionary of security group to route list
        """
        routes = {}
        for group, router in self.routers.items():
            route_list = []
            for route in router.routes:
                if hasattr(route, "path") and hasattr(route, "methods"):
                    for method in route.methods:
                        route_list.append(f"{method} {route.path}")
            routes[group.value] = route_list
        return routes
