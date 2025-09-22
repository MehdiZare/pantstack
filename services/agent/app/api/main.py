"""
Agent Service - Main API Application
"""

from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from structlog import get_logger

logger = get_logger(__name__)


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


# In-memory task store (for development)
tasks: Dict[str, TaskResponse] = {}
task_counter = 0


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting Agent Service API")
    yield
    # Shutdown
    logger.info("Shutting down Agent Service API")


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
async def create_task(
    task: TaskRequest, background_tasks: BackgroundTasks
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

    # In production, this would queue the task to Celery or similar
    logger.info(
        "Task created",
        task_id=task_id,
        task_type=task.task_type,
        priority=task.priority.value,
    )

    # Simulate task execution in background
    background_tasks.add_task(execute_task, task_id, task.payload)

    return task_response


@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str) -> TaskResponse:
    """Get task information by ID"""
    if task_id not in tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
        )

    return tasks[task_id]


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
    # Mock implementation
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


# Background task executor (mock implementation)
async def execute_task(task_id: str, payload: Dict[str, Any]):
    """Execute a task (mock implementation)"""
    import asyncio

    if task_id in tasks:
        task = tasks[task_id]
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow()
        task.attempts += 1

        # Simulate task execution
        await asyncio.sleep(2)

        # Mock success/failure (90% success rate)
        import random

        if random.random() < 0.9:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            task.result = {"output": "Task completed successfully", "payload": payload}
        else:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            task.error = "Mock task failure"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info",
    )
