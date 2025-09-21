"""
API Service Public Interface

This module exposes the public API of the API service that other services can use.
"""

from fastapi import APIRouter

# Create router for API service endpoints
api_router = APIRouter()


@api_router.get("/info")
async def get_api_info():
    """Get information about the API service"""
    return {
        "service": "api",
        "version": "1.0.0",
        "status": "operational"
    }


# Export public interface
__all__ = ["api_router"]