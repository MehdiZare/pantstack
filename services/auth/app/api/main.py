"""Auth service API endpoints."""

from contextlib import asynccontextmanager
from typing import Dict

import uvicorn
from dependency_injector.wiring import Provide, inject
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr

from ...domain.services import AuthenticationService, TokenService, UserService
from ...lib.core.container import ApplicationContainer, get_container


# Request/Response models
class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str
    confirm_password: str


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
    container = get_container()
    app.state.container = container
    yield
    # Shutdown
    print("Shutting down Auth Service")
    if hasattr(app.state, "container"):
        await app.state.container.shutdown_resources()


# Create FastAPI application
app = FastAPI(
    title="Auth Service",
    version="1.0.0",
    description="Authentication and authorization service with DDD architecture",
    lifespan=lifespan,
)

# Wire the container to the app
container = get_container()
app.container = container
container.wire(modules=[__name__])


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
@inject
async def register(
    request: RegisterRequest,
    auth_service=Depends(Provide[ApplicationContainer.service.auth_service]),
) -> Dict[str, str]:
    """Register a new user.

    Args:
        request: Registration request
        auth_service: Injected auth service

    Returns:
        Registration response

    Raises:
        HTTPException: If registration fails
    """
    try:
        from ...lib.modules.auth.schemas import RegisterRequest as AuthRegisterRequest

        auth_request = AuthRegisterRequest(
            email=request.email,
            password=request.password,
            confirm_password=request.confirm_password,
            first_name=request.username,  # Map username to first_name
            last_name="",  # Default empty last_name
        )
        response = await auth_service.register(auth_request)
        return {
            "status": "registered",
            "user_id": response.user_id,
            "email": response.email,
            "message": "User registered successfully. Please verify your email.",
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed",
        )


@app.post("/login", response_model=AuthResponse)
@inject
async def login(
    request: LoginRequest,
    auth_service=Depends(Provide[ApplicationContainer.service.auth_service]),
) -> AuthResponse:
    """Authenticate a user.

    Args:
        request: Login request
        auth_service: Injected auth service

    Returns:
        Authentication response with access token

    Raises:
        HTTPException: If authentication fails
    """
    try:
        from ...lib.modules.auth.schemas import LoginRequest as AuthLoginRequest

        auth_request = AuthLoginRequest(email=request.email, password=request.password)
        response = await auth_service.login(auth_request)

        return AuthResponse(
            access_token=response.tokens.access_token, user_id=response.user_id
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


@app.post("/verify", response_model=Dict[str, any])
@inject
async def verify(
    request: TokenVerifyRequest,
    auth_service=Depends(Provide[ApplicationContainer.service.auth_service]),
) -> Dict[str, any]:
    """Verify a token.

    Args:
        request: Token verification request
        auth_service: Injected auth service

    Returns:
        Token verification response

    Raises:
        HTTPException: If token is invalid
    """
    try:
        response = await auth_service.verify_token(request.token)

        if not response.valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        return {
            "valid": response.valid,
            "user_id": response.user_id,
            "email": response.email,
            "expires_at": (
                response.expires_at.isoformat() if response.expires_at else None
            ),
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )


@app.post("/refresh", response_model=AuthResponse)
@inject
async def refresh_token(
    refresh_token: str,
    auth_service=Depends(Provide[ApplicationContainer.service.auth_service]),
) -> AuthResponse:
    """Refresh an access token.

    Args:
        refresh_token: Refresh token
        auth_service: Injected auth service

    Returns:
        New access token

    Raises:
        HTTPException: If refresh fails
    """
    try:
        response = await auth_service.refresh_token(refresh_token)

        return AuthResponse(
            access_token=response.access_token,
            user_id="",  # User ID not available in refresh response
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@app.get("/users/me")
@inject
async def get_current_user(
    token: str,
    auth_service=Depends(Provide[ApplicationContainer.service.auth_service]),
    user_service=Depends(Provide[ApplicationContainer.service.user_service]),
) -> Dict[str, any]:
    """Get current user information.

    Args:
        token: Access token
        auth_service: Injected auth service
        user_service: Injected user service

    Returns:
        User information

    Raises:
        HTTPException: If token is invalid
    """
    try:
        token_response = await auth_service.verify_token(token)

        if not token_response.valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        # Get user details from user service
        from ...lib.core.config import AuthConfig
        from ...lib.core.database import get_supabase_client
        from ...lib.modules.users.repositories import UserRepository

        config = AuthConfig()
        db = get_supabase_client(config.database)
        user_repo = UserRepository(db)
        user = await user_repo.get(token_response.user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        return {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user.role.value if hasattr(user.role, "value") else str(user.role),
            "is_active": user.is_active,
            "is_verified": user.is_verified,
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


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
