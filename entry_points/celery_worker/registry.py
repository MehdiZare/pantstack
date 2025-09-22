"""Celery task registry for discovering tasks from all services."""

import importlib
from typing import Dict, List

from celery import Celery
from kombu import Queue

from shared.core.discovery import AutoDiscovery
from shared.core.registry import ServiceManifest, ServiceRegistry


class CeleryRegistry(ServiceRegistry):
    """Registry for Celery tasks from all services."""

    def __init__(self, app: Celery):
        """Initialize Celery registry.

        Args:
            app: Celery application instance
        """
        super().__init__()
        self.app = app
        self.tasks: Dict[str, any] = {}
        self.queues: List[Queue] = []
        self.routes: Dict[str, Dict[str, str]] = {}

    def discover_services(self) -> List[ServiceManifest]:
        """Discover all services with Celery tasks.

        Returns:
            List of service manifests
        """
        services = AutoDiscovery.discover_services()

        for service_name in services:
            manifest = AutoDiscovery.load_service_manifest(service_name, "tasks")
            if manifest:
                self.register(manifest)
                self._register_tasks(service_name, manifest)

        # Configure Celery with discovered tasks
        self._configure_celery()

        return self.get_all_manifests()

    def _register_tasks(self, service_name: str, manifest: ServiceManifest) -> None:
        """Register tasks from a service manifest.

        Args:
            service_name: Name of the service
            manifest: Service manifest containing task information
        """
        # Import task modules
        if manifest.task_modules:
            for module_name in manifest.task_modules:
                try:
                    module_path = f"services.{service_name}.src.tasks.{module_name}"
                    module = importlib.import_module(module_path)

                    # Find all tasks in the module
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if hasattr(attr, "delay"):  # It's a Celery task
                            task_name = f"{service_name}.{attr_name}"
                            self.tasks[task_name] = attr
                            print(f"  ✅ Registered task: {task_name}")

                except ImportError as e:
                    print(f"  ⚠️ Failed to import {module_path}: {e}")

        # Register individual tasks
        if manifest.tasks:
            for task_def in manifest.tasks:
                task_name = f"{service_name}.{task_def.name}"
                self.tasks[task_name] = task_def.task_func

                # Add task routing
                if task_def.queue != "default":
                    self.routes[task_name] = {"queue": task_def.queue}
                else:
                    self.routes[task_name] = {"queue": service_name}

        # Create service-specific queue
        queue = Queue(
            name=service_name,
            routing_key=f"{service_name}.*",
            queue_arguments={
                "x-max-priority": 10,  # Enable priority queue
            },
        )
        self.queues.append(queue)
        print(f"  📦 Created queue: {service_name}")

    def _configure_celery(self) -> None:
        """Configure Celery app with discovered tasks and queues."""
        # Update task routes
        self.app.conf.task_routes.update(self.routes)

        # Set queues
        self.app.conf.task_queues = self.queues

        # Add default queue if not present
        if not any(q.name == "default" for q in self.queues):
            self.queues.append(Queue("default", routing_key="default"))

        print(f"\n📊 Celery Configuration:")
        print(f"  - Tasks registered: {len(self.tasks)}")
        print(f"  - Queues created: {len(self.queues)}")
        print(f"  - Routes configured: {len(self.routes)}")

    def get_all_tasks(self) -> Dict[str, List[str]]:
        """Get all registered tasks grouped by service.

        Returns:
            Dictionary of service to task list
        """
        tasks_by_service: Dict[str, List[str]] = {}

        for task_name in self.tasks.keys():
            service_name = task_name.split(".")[0]
            if service_name not in tasks_by_service:
                tasks_by_service[service_name] = []
            tasks_by_service[service_name].append(task_name)

        return tasks_by_service
