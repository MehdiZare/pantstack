"""Auth service API endpoints."""

from contextlib import asynccontextmanager
from typing import Dict, Optional

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr

from ...adapters.repositories import InMemoryTokenRepository, InMemoryUserRepository
from ...domain.models import UserRole
from ...domain.services import AuthenticationService, TokenService, UserService

# Initialize repositories (in production, these would be injected)
user_repo = InMemoryUserRepository()
token_repo = InMemoryTokenRepository()

# Initialize domain services
auth_service = AuthenticationService(user_repo, token_repo)
user_service = UserService(user_repo)
token_service = TokenService(token_repo)


# Request/Response models
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenVerifyRequest(BaseModel):
    token: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    print("Starting Auth Service")
    yield
    # Shutdown
    print("Shutting down Auth Service")


# Create FastAPI application
app = FastAPI(
    title="Auth Service",
    version="1.0.0",
    description="Authentication and authorization service with DDD architecture",
    lifespan=lifespan,
)


@app.get("/healthz")
async def healthz() -> Dict[str, str]:
    """Health check endpoint.

    Returns:
        Status dictionary
    """
    return {"status": "healthy", "service": "auth", "version": "1.0.0"}


@app.post(
    "/register", response_model=Dict[str, str], status_code=status.HTTP_201_CREATED
)
async def register(request: RegisterRequest) -> Dict[str, str]:
    """Register a new user.

    Args:
        request: Registration request

    Returns:
        Registration response

    Raises:
        HTTPException: If registration fails
    """
    try:
        user = await auth_service.register(
            email=request.email, username=request.username, password=request.password
        )
        return {
            "status": "registered",
            "user_id": user.id,
            "email": user.email,
            "message": "User registered successfully. Please verify your email.",
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@app.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest) -> AuthResponse:
    """Authenticate a user.

    Args:
        request: Login request

    Returns:
        Authentication response with access token

    Raises:
        HTTPException: If authentication fails
    """
    user, token = await auth_service.authenticate(
        email=request.email, password=request.password
    )

    if not user or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Record login
    await user_service.record_login(user.id)

    return AuthResponse(access_token=token.token, user_id=user.id)


@app.post("/verify", response_model=Dict[str, any])
async def verify(request: TokenVerifyRequest) -> Dict[str, any]:
    """Verify a token.

    Args:
        request: Token verification request

    Returns:
        Token verification response

    Raises:
        HTTPException: If token is invalid
    """
    user = await auth_service.verify_token(request.token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    return {
        "valid": True,
        "user_id": user.id,
        "email": user.email,
        "role": user.role.value,
    }


@app.post("/refresh", response_model=AuthResponse)
async def refresh_token(refresh_token: str) -> AuthResponse:
    """Refresh an access token.

    Args:
        refresh_token: Refresh token

    Returns:
        New access token

    Raises:
        HTTPException: If refresh fails
    """
    new_token = await auth_service.refresh_token(refresh_token)

    if not new_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    return AuthResponse(access_token=new_token.token, user_id=new_token.user_id)


@app.get("/users/me")
async def get_current_user(token: str) -> Dict[str, any]:
    """Get current user information.

    Args:
        token: Access token

    Returns:
        User information

    Raises:
        HTTPException: If token is invalid
    """
    user = await auth_service.verify_token(token)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )

    return {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "role": user.role.value,
        "status": user.status.value,
        "email_verified": user.email_verified,
    }


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
