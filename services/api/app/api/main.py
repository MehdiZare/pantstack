"""
API Service - Main Application Entry Point
"""
from contextlib import asynccontextmanager
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from structlog import get_logger

logger = get_logger(__name__)


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = "healthy"
    service: str = "api"
    version: str = "1.0.0"
    details: Dict[str, Any] = {}


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    message: str
    details: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting API service", service="api")
    yield
    # Shutdown
    logger.info("Shutting down API service", service="api")


app = FastAPI(
    title="API Service",
    description="Main API gateway service for the Pantstack platform",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "message": exc.detail,
            "details": {"status_code": exc.status_code, "path": str(request.url)},
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=str(request.url),
        exc_info=exc,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_error",
            "message": "An internal server error occurred",
            "details": {},
        },
    )


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to API Service",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        service="api",
        version="1.0.0",
        details={
            "uptime": "running",
            "environment": "development",
        }
    )


@app.get("/api/v1/status", response_model=Dict[str, Any])
async def api_status():
    """API status endpoint"""
    return {
        "status": "operational",
        "version": "1.0.0",
        "api_version": "v1",
        "services": {
            "api": "healthy",
            "database": "connected",
            "cache": "connected",
        }
    }


# API Routes would be mounted here from various services
# Example:
# from services.auth.public import auth_router
# from services.web.public import web_router
# app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
# app.include_router(web_router, prefix="/api/v1/web", tags=["Web"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )