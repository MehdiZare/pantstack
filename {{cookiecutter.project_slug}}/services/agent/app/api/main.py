"""
Agent Service - Main API Application
"""

from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from structlog import get_logger

from ...lib.core.container import ApplicationContainer, get_container

try:
    from celery import current_app as celery_app

    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    celery_app = None

logger = get_logger(__name__)

# Initialize container
container = get_container()


# Models
class TaskStatus(str, Enum):
    """Task execution status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    """Task priority levels"""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class TaskRequest(BaseModel):
    """Request model for creating a task"""

    name: str = Field(..., description="Task name")
    task_type: str = Field(..., description="Type of task to execute")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Task payload")
    priority: TaskPriority = Field(
        default=TaskPriority.NORMAL, description="Task priority"
    )
    schedule_at: Optional[datetime] = Field(
        None, description="Schedule task for future execution"
    )
    retry_count: int = Field(default=3, description="Number of retries on failure")


class TaskResponse(BaseModel):
    """Response model for task information"""

    id: str
    name: str
    task_type: str
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int
    attempts: int = 0
    celery_task_id: Optional[str] = None


class AgentInfo(BaseModel):
    """Agent information model"""

    id: str
    name: str
    status: str
    capabilities: List[str]
    active_tasks: int
    completed_tasks: int
    failed_tasks: int
    uptime_seconds: float


# In-memory task store
tasks: Dict[str, TaskResponse] = {}
task_counter = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting Agent Service API")
    await container.init_resources()
    container.wire(modules=[__name__])

    # Inject Celery app if available
    if celery_app:
        from dependency_injector import providers

        container.infrastructure.celery_app.override(providers.Object(celery_app))

    yield
    # Shutdown
    logger.info("Shutting down Agent Service API")
    await container.shutdown_resources()


app = FastAPI(
    title="Agent Service",
    description="Distributed task execution and agent management service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "service": "agent",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
    }


@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "agent",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {
            "database": "connected",
            "worker_pool": "healthy",
            "message_queue": "connected",
        },
    }


@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
@inject
async def create_task(
    task: TaskRequest,
    background_tasks: BackgroundTasks,
    task_service=Depends(Provide[ApplicationContainer.services.task_service]),
) -> TaskResponse:
    """Create a new task for execution"""
    global task_counter
    task_counter += 1
    task_id = f"task_{task_counter:06d}"

    task_response = TaskResponse(
        id=task_id,
        name=task.name,
        task_type=task.task_type,
        status=TaskStatus.PENDING,
        priority=task.priority,
        created_at=datetime.utcnow(),
        retry_count=task.retry_count,
    )

    tasks[task_id] = task_response

    # Try to use Celery if available
    if CELERY_AVAILABLE and celery_app:
        try:
            # Map task types to Celery tasks
            celery_task_map = {
                "data_processing": "agent.process_data",
                "workflow": "agent.execute_workflow",
                "report": "agent.generate_report",
                "batch": "agent.batch_process",
                "sync": "agent.sync_external_data",
                "notification": "agent.send_notification",
                "cleanup": "agent.cleanup_old_data",
                "health_check": "agent.health_check",
            }

            celery_task_name = celery_task_map.get(task.task_type, "agent.process_data")

            # Send task to Celery
            celery_result = celery_app.send_task(
                celery_task_name,
                kwargs=(
                    {"data": task.payload}
                    if "data" in celery_task_name
                    else {"parameters": task.payload}
                ),
                queue="agent" if "agent" in celery_task_name else "default",
                task_id=task_id,
            )

            # Store Celery task ID for tracking
            task_response.celery_task_id = celery_result.id
            logger.info(
                "Task sent to Celery",
                task_id=task_id,
                celery_task_id=celery_result.id,
                task_type=task.task_type,
            )
        except Exception as e:
            logger.warning(
                f"Failed to send task to Celery: {e}, falling back to background task"
            )
            background_tasks.add_task(execute_task, task_id, task.payload)
    else:
        # Fallback to background task
        logger.info(
            "Task created (Celery not available)",
            task_id=task_id,
            task_type=task.task_type,
            priority=task.priority.value,
        )
        background_tasks.add_task(execute_task, task_id, task.payload)

    return task_response


@app.get("/tasks/{task_id}", response_model=TaskResponse)
@inject
async def get_task(
    task_id: str,
    task_service=Depends(Provide[ApplicationContainer.services.task_service]),
) -> TaskResponse:
    """Get task information by ID"""
    if task_id not in tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
        )

    task = tasks[task_id]

    # If task has Celery ID, try to get status from Celery
    if CELERY_AVAILABLE and hasattr(task, "celery_task_id") and task.celery_task_id:
        try:
            from celery.result import AsyncResult

            celery_result = AsyncResult(task.celery_task_id, app=celery_app)

            if celery_result.ready():
                if celery_result.successful():
                    task.status = TaskStatus.COMPLETED
                    task.result = celery_result.result
                    task.completed_at = datetime.utcnow()
                elif celery_result.failed():
                    task.status = TaskStatus.FAILED
                    task.error = str(celery_result.info)
                    task.completed_at = datetime.utcnow()
            elif celery_result.state == "PENDING":
                task.status = TaskStatus.PENDING
            else:
                task.status = TaskStatus.RUNNING
                task.started_at = task.started_at or datetime.utcnow()
        except Exception as e:
            logger.warning(f"Failed to get Celery task status: {e}")

    return task


@app.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    limit: int = 100,
    offset: int = 0,
) -> List[TaskResponse]:
    """List tasks with optional filtering"""
    filtered_tasks = list(tasks.values())

    if status:
        filtered_tasks = [t for t in filtered_tasks if t.status == status]

    if priority:
        filtered_tasks = [t for t in filtered_tasks if t.priority == priority]

    return filtered_tasks[offset : offset + limit]


@app.put("/tasks/{task_id}/cancel", response_model=TaskResponse)
async def cancel_task(task_id: str) -> TaskResponse:
    """Cancel a pending or running task"""
    if task_id not in tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
        )

    task = tasks[task_id]

    if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel task in {task.status} status",
        )

    task.status = TaskStatus.CANCELLED
    logger.info("Task cancelled", task_id=task_id)

    return task


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a completed or cancelled task"""
    if task_id not in tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
        )

    task = tasks[task_id]

    if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete task in {task.status} status",
        )

    del tasks[task_id]
    logger.info("Task deleted", task_id=task_id)

    return {"message": f"Task {task_id} deleted"}


@app.get("/agents", response_model=List[AgentInfo])
async def list_agents() -> List[AgentInfo]:
    """List all available agents"""
    # In production, this would query the actual agent pool
    return [
        AgentInfo(
            id="agent_001",
            name="Worker-1",
            status="active",
            capabilities=["data_processing", "api_calls", "file_operations"],
            active_tasks=2,
            completed_tasks=150,
            failed_tasks=3,
            uptime_seconds=3600.0,
        ),
        AgentInfo(
            id="agent_002",
            name="Worker-2",
            status="active",
            capabilities=["ml_inference", "data_analysis", "report_generation"],
            active_tasks=1,
            completed_tasks=89,
            failed_tasks=1,
            uptime_seconds=1800.0,
        ),
    ]


@app.get("/agents/{agent_id}", response_model=AgentInfo)
async def get_agent(agent_id: str) -> AgentInfo:
    """Get specific agent information"""
    if agent_id not in ["agent_001", "agent_002"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Agent {agent_id} not found"
        )

    return AgentInfo(
        id=agent_id,
        name=f"Worker-{agent_id[-1]}",
        status="active",
        capabilities=["data_processing", "api_calls"],
        active_tasks=1,
        completed_tasks=100,
        failed_tasks=2,
        uptime_seconds=3600.0,
    )


@app.post("/agents/{agent_id}/restart")
async def restart_agent(agent_id: str):
    """Restart a specific agent"""
    logger.info("Restarting agent", agent_id=agent_id)
    return {"message": f"Agent {agent_id} restart initiated"}


# Background task executor
async def execute_task(task_id: str, payload: Dict[str, Any]):
    """Execute a task"""
    import asyncio

    if task_id in tasks:
        task = tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        task.attempts += 1

        # Simulate task execution
        await asyncio.sleep(2)

        # Simulate success/failure (90% success rate)
        import random

        if random.random() < 0.9:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = {"output": "Task completed successfully", "payload": payload}
        else:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.error = "Task execution failed"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
    )
