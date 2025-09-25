"""Module discovery system for services."""

import importlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol

from fastapi import APIRouter

logger = logging.getLogger(__name__)


class ModuleInterface(Protocol):
    """Protocol defining the interface all modules must implement."""

    @property
    def name(self) -> str:
        """Module name."""
        ...

    def get_routes(self) -> Optional[APIRouter]:
        """Get module API routes."""
        ...

    def get_tasks(self) -> List[str]:
        """Get module Celery tasks."""
        ...

    def get_handlers(self) -> Dict[str, Any]:
        """Get module event handlers."""
        ...

    def initialize(self) -> None:
        """Initialize module resources."""
        ...

    def shutdown(self) -> None:
        """Clean up module resources."""
        ...


class ModuleDiscovery:
    """Service module discovery and management."""

    def __init__(self, service_name: str):
        """Initialize module discovery for a service.

        Args:
            service_name: Name of the service
        """
        self.service_name = service_name
        self.modules: Dict[str, ModuleInterface] = {}
        self._discovered = False

    def discover_modules(
        self, base_path: Optional[Path] = None
    ) -> Dict[str, ModuleInterface]:
        """Discover all modules for the service.

        Args:
            base_path: Optional base path for module discovery

        Returns:
            Dictionary of module name to module instance
        """
        if self._discovered:
            return self.modules

        if base_path is None:
            # Default to services/{service_name}/lib/modules
            base_path = Path(f"services/{self.service_name}/lib/modules")

        if not base_path.exists():
            logger.warning(f"Module path {base_path} does not exist")
            return self.modules

        # Discover modules by looking for subdirectories with module.py
        for module_dir in base_path.iterdir():
            if module_dir.is_dir() and not module_dir.name.startswith("_"):
                module_file = module_dir / "module.py"
                if module_file.exists():
                    try:
                        module = self._load_module(module_dir.name)
                        if module:
                            self.modules[module.name] = module
                            logger.info(f"Discovered module: {module.name}")
                    except Exception as e:
                        logger.error(f"Failed to load module {module_dir.name}: {e}")

        self._discovered = True
        return self.modules

    def _load_module(self, module_name: str) -> Optional[ModuleInterface]:
        """Load a specific module.

        Args:
            module_name: Name of the module to load

        Returns:
            Module instance or None if loading fails
        """
        try:
            # Import the module
            module_path = f"services.{self.service_name}.lib.modules.{module_name}"
            imported = importlib.import_module(module_path)

            # Look for a class that ends with "Module"
            module_class_name = f"{module_name.title().replace('_', '')}Module"
            module_class = getattr(imported, module_class_name, None)

            if module_class:
                return module_class()
            else:
                logger.warning(f"No {module_class_name} found in {module_path}")
                return None
        except ImportError as e:
            logger.error(f"Could not import module {module_name}: {e}")
            return None

    def get_all_routes(self) -> List[APIRouter]:
        """Get all routes from discovered modules.

        Returns:
            List of FastAPI routers
        """
        routes = []
        for module in self.modules.values():
            router = module.get_routes()
            if router:
                routes.append(router)
        return routes

    def get_all_tasks(self) -> List[str]:
        """Get all tasks from discovered modules.

        Returns:
            List of task names
        """
        tasks = []
        for module in self.modules.values():
            module_tasks = module.get_tasks()
            if module_tasks:
                tasks.extend(module_tasks)
        return tasks

    def get_all_handlers(self) -> Dict[str, Any]:
        """Get all event handlers from discovered modules.

        Returns:
            Dictionary of event type to handler
        """
        handlers = {}
        for module in self.modules.values():
            module_handlers = module.get_handlers()
            if module_handlers:
                handlers.update(module_handlers)
        return handlers

    def initialize_all(self) -> None:
        """Initialize all discovered modules."""
        for module in self.modules.values():
            try:
                module.initialize()
                logger.info(f"Initialized module: {module.name}")
            except Exception as e:
                logger.error(f"Failed to initialize module {module.name}: {e}")

    def shutdown_all(self) -> None:
        """Shutdown all discovered modules."""
        for module in self.modules.values():
            try:
                module.shutdown()
                logger.info(f"Shutdown module: {module.name}")
            except Exception as e:
                logger.error(f"Failed to shutdown module {module.name}: {e}")

    def get_module(self, name: str) -> Optional[ModuleInterface]:
        """Get a specific module by name.

        Args:
            name: Module name

        Returns:
            Module instance or None
        """
        return self.modules.get(name)

    def list_modules(self) -> List[str]:
        """List all discovered module names.

        Returns:
            List of module names
        """
        return list(self.modules.keys())


class SelectiveModuleLoader:
    """Load only specific modules for optimized entry points."""

    def __init__(self, service_name: str):
        """Initialize selective module loader.

        Args:
            service_name: Name of the service
        """
        self.service_name = service_name
        self.discovery = ModuleDiscovery(service_name)

    def load_modules(self, module_names: List[str]) -> Dict[str, ModuleInterface]:
        """Load only specified modules.

        Args:
            module_names: List of module names to load

        Returns:
            Dictionary of loaded modules
        """
        modules = {}
        for name in module_names:
            try:
                module = self._load_single_module(name)
                if module:
                    modules[name] = module
                    logger.info(f"Selectively loaded module: {name}")
            except Exception as e:
                logger.error(f"Failed to load module {name}: {e}")
        return modules

    def _load_single_module(self, module_name: str) -> Optional[ModuleInterface]:
        """Load a single module.

        Args:
            module_name: Name of the module

        Returns:
            Module instance or None
        """
        module_path = f"services.{self.service_name}.lib.modules.{module_name}"
        try:
            imported = importlib.import_module(module_path)
            module_class_name = f"{module_name.title().replace('_', '')}Module"
            module_class = getattr(imported, module_class_name, None)

            if module_class:
                return module_class()
            return None
        except ImportError:
            return None

    def load_for_api(self) -> Dict[str, ModuleInterface]:
        """Load all modules for API entry point.

        Returns:
            All available modules
        """
        self.discovery.discover_modules()
        return self.discovery.modules

    def load_for_lambda(
        self, required_modules: List[str]
    ) -> Dict[str, ModuleInterface]:
        """Load minimal modules for Lambda entry point.

        Args:
            required_modules: List of required module names

        Returns:
            Only required modules
        """
        return self.load_modules(required_modules)

    def load_for_worker(self) -> Dict[str, ModuleInterface]:
        """Load modules with tasks for worker entry point.

        Returns:
            Modules that have tasks
        """
        self.discovery.discover_modules()
        worker_modules = {}
        for name, module in self.discovery.modules.items():
            if module.get_tasks():
                worker_modules[name] = module
        return worker_modules
