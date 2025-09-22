"""Dependency injection container for agent service."""

from dependency_injector import containers, providers

from shared.core.container import ApplicationContainer as BaseApplicationContainer
from shared.core.container import (
    InfrastructureContainer,
)
from shared.core.container import RepositoryContainer as BaseRepositoryContainer
from shared.core.container import ServiceContainer as BaseServiceContainer


class AgentConfig:
    """Agent service configuration."""

    def __init__(self):
        self.service_name = "agent"
        self.version = "1.0.0"
        self.environment = "development"

        # Database config
        self.database = {
            "url": "postgresql://localhost:5432/agent_db",
        }

        # Redis config
        self.redis = {
            "host": "localhost",
            "port": 6379,
            "db": 1,
        }

        # AWS config
        self.aws = {
            "region": "us-east-1",
            "endpoint_url": "http://localhost:4566",
        }

        # Celery config
        self.celery = {
            "broker_url": "redis://localhost:6379/0",
            "result_backend": "redis://localhost:6379/0",
        }


class TaskRepository:
    """Repository for task management."""

    def __init__(self, db_client, cache_client):
        self.db = db_client
        self.cache = cache_client
        self._tasks = {}  # In-memory storage for now

    async def create(self, task_data: dict) -> dict:
        """Create a new task."""
        task_id = f"task_{len(self._tasks) + 1:06d}"
        task = {
            "id": task_id,
            **task_data,
            "status": "pending",
            "created_at": "2024-01-01T00:00:00",
        }
        self._tasks[task_id] = task
        return task

    async def get(self, task_id: str) -> dict:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    async def update(self, task_id: str, update_data: dict) -> dict:
        """Update a task."""
        if task_id in self._tasks:
            self._tasks[task_id].update(update_data)
            return self._tasks[task_id]
        return None

    async def list(self, **filters) -> list:
        """List tasks with optional filters."""
        tasks = list(self._tasks.values())

        # Apply filters
        if "status" in filters:
            tasks = [t for t in tasks if t.get("status") == filters["status"]]
        if "priority" in filters:
            tasks = [t for t in tasks if t.get("priority") == filters["priority"]]

        return tasks


class WorkflowRepository:
    """Repository for workflow management."""

    def __init__(self, db_client):
        self.db = db_client
        self._workflows = {}

    async def create(self, workflow_data: dict) -> dict:
        """Create a new workflow."""
        workflow_id = f"workflow_{len(self._workflows) + 1:06d}"
        workflow = {
            "id": workflow_id,
            **workflow_data,
            "status": "created",
        }
        self._workflows[workflow_id] = workflow
        return workflow

    async def get(self, workflow_id: str) -> dict:
        """Get a workflow by ID."""
        return self._workflows.get(workflow_id)


class TaskService:
    """Service for task management."""

    def __init__(self, task_repo: TaskRepository, celery_app=None):
        self.task_repo = task_repo
        self.celery_app = celery_app

    async def create_task(self, task_data: dict) -> dict:
        """Create and optionally queue a task."""
        task = await self.task_repo.create(task_data)

        # Queue to Celery if available
        if self.celery_app and task_data.get("execute_async"):
            try:
                celery_task = self.celery_app.send_task(
                    f"agent.{task_data.get('task_type', 'process_data')}",
                    kwargs={"data": task_data.get("payload", {})},
                    task_id=task["id"],
                )
                task["celery_task_id"] = celery_task.id
            except Exception as e:
                print(f"Failed to queue task to Celery: {e}")

        return task

    async def get_task_status(self, task_id: str) -> dict:
        """Get task status."""
        task = await self.task_repo.get(task_id)

        if task and self.celery_app and task.get("celery_task_id"):
            try:
                from celery.result import AsyncResult

                result = AsyncResult(task["celery_task_id"], app=self.celery_app)

                if result.ready():
                    task["status"] = "completed" if result.successful() else "failed"
                    task["result"] = result.result if result.successful() else None
                    task["error"] = str(result.info) if result.failed() else None
                elif result.state == "PENDING":
                    task["status"] = "pending"
                else:
                    task["status"] = "running"
            except Exception:
                pass

        return task

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        task = await self.task_repo.get(task_id)

        if task and task.get("status") in ["pending", "running"]:
            await self.task_repo.update(task_id, {"status": "cancelled"})

            # Cancel Celery task if applicable
            if self.celery_app and task.get("celery_task_id"):
                try:
                    self.celery_app.control.revoke(
                        task["celery_task_id"], terminate=True
                    )
                except Exception:
                    pass

            return True
        return False


class WorkflowService:
    """Service for workflow orchestration."""

    def __init__(self, workflow_repo: WorkflowRepository, task_service: TaskService):
        self.workflow_repo = workflow_repo
        self.task_service = task_service

    async def create_workflow(self, workflow_data: dict) -> dict:
        """Create a new workflow."""
        return await self.workflow_repo.create(workflow_data)

    async def execute_workflow(self, workflow_id: str) -> dict:
        """Execute a workflow."""
        workflow = await self.workflow_repo.get(workflow_id)

        if workflow:
            # Execute workflow steps
            for step in workflow.get("steps", []):
                task_data = {
                    "name": step.get("name"),
                    "task_type": step.get("type"),
                    "payload": step.get("params"),
                    "execute_async": True,
                }
                await self.task_service.create_task(task_data)

            workflow["status"] = "executing"
            return workflow

        return None


class AgentRepositoryContainer(BaseRepositoryContainer):
    """Repository layer container for agent service."""

    infrastructure = providers.DependenciesContainer()

    # Task repository
    task_repository = providers.Singleton(
        TaskRepository,
        db_client=infrastructure.provided.database_client,
        cache_client=infrastructure.provided.redis_client,
    )

    # Workflow repository
    workflow_repository = providers.Singleton(
        WorkflowRepository,
        db_client=infrastructure.provided.database_client,
    )


class AgentServiceContainer(BaseServiceContainer):
    """Service layer container for agent service."""

    repositories = providers.DependenciesContainer()
    infrastructure = providers.DependenciesContainer()

    # Task service
    task_service = providers.Factory(
        TaskService,
        task_repo=repositories.task_repository,
        celery_app=infrastructure.provided.celery_app,
    )

    # Workflow service
    workflow_service = providers.Factory(
        WorkflowService,
        workflow_repo=repositories.workflow_repository,
        task_service=task_service,
    )


class AgentInfrastructureContainer(InfrastructureContainer):
    """Infrastructure container for agent service."""

    config = providers.DependenciesContainer()

    # Database client
    database_client = providers.Singleton(
        lambda: {"connected": True},
    )

    # Redis client
    redis_client = providers.Singleton(
        lambda: {"connected": True},
    )

    # Celery app
    celery_app = providers.Singleton(
        lambda: None,  # Will be injected from environment
    )


class ApplicationContainer(BaseApplicationContainer):
    """Main container for agent service."""

    # Configuration
    config = providers.Singleton(AgentConfig)

    # Infrastructure
    infrastructure = providers.Container(
        AgentInfrastructureContainer,
        config=config,
    )

    # Repositories
    repositories = providers.Container(
        AgentRepositoryContainer,
        infrastructure=infrastructure,
    )

    # Services
    services = providers.Container(
        AgentServiceContainer,
        repositories=repositories,
        infrastructure=infrastructure,
    )

    async def init_resources(self):
        """Initialize async resources."""
        print("Initializing Agent service resources...")
        # Add initialization logic here

    async def shutdown_resources(self):
        """Shutdown async resources."""
        print("Shutting down Agent service resources...")
        # Add cleanup logic here


# Global container instance
_container: ApplicationContainer = None


def get_container() -> ApplicationContainer:
    """Get or create the container instance."""
    global _container
    if _container is None:
        _container = ApplicationContainer()
    return _container
