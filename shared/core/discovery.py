"""Auto-discovery utilities for services and components."""

import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Any, List, Optional

from .registry import ServiceManifest


class AutoDiscovery:
    """Auto-discover services and their components."""

    @staticmethod
    def discover_services(base_path: str = "services") -> List[str]:
        """Discover all services in the services directory.

        Args:
            base_path: Path to services directory

        Returns:
            List of service names
        """
        services = []
        services_path = Path(base_path)

        if not services_path.exists():
            print(f"⚠️ Services directory not found: {base_path}")
            return services

        for service_dir in services_path.iterdir():
            if service_dir.is_dir() and not service_dir.name.startswith("_"):
                # Check if it looks like a service (has expected structure)
                if (service_dir / "src").exists() or (service_dir / "lib").exists():
                    services.append(service_dir.name)
                    print(f"🔍 Discovered service: {service_dir.name}")

        return services

    @staticmethod
    def load_service_manifest(
        service_name: str, component: str, base_path: str = "services"
    ) -> Optional[ServiceManifest]:
        """Load manifest from a service component.

        Args:
            service_name: Name of the service
            component: Component type (api, tasks, handlers)
            base_path: Base path to services

        Returns:
            ServiceManifest if found, None otherwise
        """
        try:
            # Try different manifest locations
            manifest_paths = [
                f"{base_path}.{service_name}.src.{component}.manifest",
                f"{base_path}.{service_name}.{component}.manifest",
                f"{service_name}.src.{component}.manifest",
            ]

            for module_path in manifest_paths:
                try:
                    module = importlib.import_module(module_path)
                    if hasattr(module, "manifest"):
                        manifest = module.manifest
                        print(f"✅ Loaded manifest: {service_name}/{component}")
                        return manifest
                except (ImportError, AttributeError):
                    continue

            # If no manifest found, try to auto-generate basic one
            return AutoDiscovery._generate_manifest(service_name, component, base_path)

        except Exception as e:
            print(f"❌ Failed to load manifest for {service_name}/{component}: {e}")
            return None

    @staticmethod
    def _generate_manifest(
        service_name: str, component: str, base_path: str = "services"
    ) -> Optional[ServiceManifest]:
        """Generate a basic manifest by scanning the component directory.

        Args:
            service_name: Name of the service
            component: Component type
            base_path: Base path to services

        Returns:
            Generated ServiceManifest or None
        """
        try:
            component_path = Path(base_path) / service_name / "src" / component

            if not component_path.exists():
                return None

            # Create basic manifest
            manifest = ServiceManifest(
                service_name=service_name,
                version="0.1.0",
                description=f"Auto-generated manifest for {service_name}/{component}",
            )

            # Scan for Python files
            if component == "tasks":
                # List task modules
                task_modules = []
                for py_file in component_path.glob("*.py"):
                    if not py_file.name.startswith("_"):
                        task_modules.append(py_file.stem)
                manifest.task_modules = task_modules

            print(f"🤖 Generated manifest for {service_name}/{component}")
            return manifest

        except Exception as e:
            print(f"❌ Failed to generate manifest: {e}")
            return None

    @staticmethod
    def import_module_from_path(path: Path, module_name: str) -> Optional[Any]:
        """Import a module from a file path.

        Args:
            path: Path to the Python file
            module_name: Name to give the module

        Returns:
            Imported module or None
        """
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
                return module
        except Exception as e:
            print(f"❌ Failed to import {path}: {e}")
        return None

    @staticmethod
    def find_handlers_in_module(module: Any) -> List[tuple[str, Any]]:
        """Find all handler functions in a module.

        Args:
            module: Python module to scan

        Returns:
            List of (name, function) tuples
        """
        handlers = []
        for name in dir(module):
            if not name.startswith("_"):
                obj = getattr(module, name)
                if callable(obj):
                    # Check if it looks like a handler
                    if "handler" in name.lower() or hasattr(obj, "_is_handler"):
                        handlers.append((name, obj))
        return handlers

    @staticmethod
    def find_tasks_in_module(module: Any) -> List[tuple[str, Any]]:
        """Find all Celery tasks in a module.

        Args:
            module: Python module to scan

        Returns:
            List of (name, task) tuples
        """
        tasks = []
        for name in dir(module):
            if not name.startswith("_"):
                obj = getattr(module, name)
                # Check if it's a Celery task
                if hasattr(obj, "delay") or hasattr(obj, "apply_async"):
                    tasks.append((name, obj))
        return tasks

    @staticmethod
    def find_routes_in_module(module: Any) -> List[tuple[str, Any]]:
        """Find all route functions in a module.

        Args:
            module: Python module to scan

        Returns:
            List of (name, function) tuples
        """
        routes = []
        for name in dir(module):
            if not name.startswith("_"):
                obj = getattr(module, name)
                if callable(obj):
                    # Check if it has route decorators or looks like a route
                    if hasattr(obj, "_route_info") or any(
                        keyword in name.lower()
                        for keyword in ["get", "post", "put", "delete", "patch"]
                    ):
                        routes.append((name, obj))
        return routes
