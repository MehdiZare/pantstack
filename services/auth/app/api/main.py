"""Auth service API endpoints."""

from typing import Dict

import uvicorn
from fastapi import FastAPI, HTTPException

# Create FastAPI application
app = FastAPI(
    title="Auth Service",
    version="1.0.0",
    description="Authentication and authorization service",
)


@app.get("/healthz")
async def healthz() -> Dict[str, str]:
    """Health check endpoint.

    Returns:
        Status dictionary
    """
    return {"status": "ok", "service": "auth"}


@app.post("/register")
async def register(email: str, password: str) -> Dict[str, str]:
    """Register a new user.

    Temporarily simplified endpoint.

    Args:
        email: User email
        password: User password

    Returns:
        Registration response

    Raises:
        HTTPException: If registration fails
    """
    # TODO: Implement proper registration with dependency injection
    return {"status": "registered", "email": email}


@app.post("/login")
async def login(email: str, password: str) -> Dict[str, str]:
    """Authenticate a user.

    Temporarily simplified endpoint.

    Args:
        email: User email
        password: User password

    Returns:
        Login response

    Raises:
        HTTPException: If authentication fails
    """
    # TODO: Implement proper login with dependency injection
    return {"status": "logged_in", "email": email}


@app.post("/verify")
async def verify(token: str) -> Dict[str, bool]:
    """Verify a JWT token.

    Temporarily simplified endpoint.

    Args:
        token: JWT token

    Returns:
        Token verification response

    Raises:
        HTTPException: If token is invalid
    """
    # TODO: Implement proper token verification with dependency injection
    return {"valid": False}


def run() -> None:
    """Run the API server."""
    uvicorn.run(
        "services.auth.app.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    run()