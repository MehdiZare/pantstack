"""API routes for auth service."""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, status

from shared.core.security import User as CurrentUser
from shared.core.security import get_current_user

from services.auth.lib.core.container import AuthContainer
from services.auth.lib.modules.auth import (
    AuthService,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    TokenResponse,
)
from services.auth.lib.modules.auth.schemas import (
    EmailVerificationRequest,
    PasswordChangeRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshTokenRequest,
)
from services.auth.lib.modules.users import UserProfile, UserService, UserUpdate

# Create routers for different security groups
public_router = APIRouter(tags=["auth"])
authenticated_router = APIRouter(tags=["auth", "users"])
admin_router = APIRouter(tags=["admin"])


# Public endpoints (no auth required)
@public_router.post("/auth/register", response_model=LoginResponse)
@inject
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(Provide[AuthContainer.services.auth_service]),
) -> LoginResponse:
    """Register a new user."""
    try:
        return await auth_service.register(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@public_router.post("/auth/login", response_model=LoginResponse)
@inject
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(Provide[AuthContainer.services.auth_service]),
) -> LoginResponse:
    """Login a user."""
    try:
        return await auth_service.login(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@public_router.post("/auth/refresh", response_model=TokenResponse)
@inject
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(Provide[AuthContainer.services.auth_service]),
) -> TokenResponse:
    """Refresh access token."""
    try:
        return await auth_service.refresh_token(request.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@public_router.post("/auth/password-reset")
@inject
async def request_password_reset(
    request: PasswordResetRequest,
    auth_service: AuthService = Depends(Provide[AuthContainer.services.auth_service]),
) -> dict:
    """Request password reset."""
    await auth_service.request_password_reset(request.email)
    return {"message": "If the email exists, a reset link will be sent"}


@public_router.post("/auth/password-reset/confirm")
@inject
async def reset_password(
    request: PasswordResetConfirm,
    auth_service: AuthService = Depends(Provide[AuthContainer.services.auth_service]),
) -> dict:
    """Reset password with token."""
    try:
        await auth_service.reset_password(request.token, request.new_password)
        return {"message": "Password reset successful"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@public_router.post("/auth/verify-email")
@inject
async def verify_email(
    request: EmailVerificationRequest,
    auth_service: AuthService = Depends(Provide[AuthContainer.services.auth_service]),
) -> dict:
    """Verify email with token."""
    try:
        await auth_service.verify_email(request.token)
        return {"message": "Email verified successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Authenticated endpoints (require valid JWT)
@authenticated_router.get("/users/me", response_model=UserProfile)
@inject
async def get_my_profile(
    current_user: CurrentUser = Depends(get_current_user),
    user_service: UserService = Depends(Provide[AuthContainer.services.user_service]),
) -> UserProfile:
    """Get current user profile."""
    return await user_service.get_profile(current_user.id)


@authenticated_router.patch("/users/me", response_model=UserProfile)
@inject
async def update_my_profile(
    update_data: UserUpdate,
    current_user: CurrentUser = Depends(get_current_user),
    user_service: UserService = Depends(Provide[AuthContainer.services.user_service]),
) -> UserProfile:
    """Update current user profile."""
    return await user_service.update_profile(current_user.id, update_data)


@authenticated_router.post("/auth/logout")
@inject
async def logout(
    refresh_token: str,
    current_user: CurrentUser = Depends(get_current_user),
    auth_service: AuthService = Depends(Provide[AuthContainer.services.auth_service]),
) -> dict:
    """Logout current user."""
    await auth_service.logout(current_user.id, refresh_token)
    return {"message": "Logged out successfully"}


@authenticated_router.post("/auth/change-password")
@inject
async def change_password(
    request: PasswordChangeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    auth_service: AuthService = Depends(Provide[AuthContainer.services.auth_service]),
) -> dict:
    """Change current user's password."""
    try:
        await auth_service.change_password(
            current_user.id, request.current_password, request.new_password
        )
        return {"message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Admin endpoints (require admin role)
@admin_router.get("/users")
@inject
async def list_users(
    page: int = 1,
    page_size: int = 20,
    filter_active: bool | None = None,
    user_service: UserService = Depends(Provide[AuthContainer.services.user_service]),
):
    """List all users (admin only)."""
    return await user_service.list_all_users(page, page_size, filter_active)


@admin_router.get("/users/{user_id}")
@inject
async def get_user(
    user_id: str,
    user_service: UserService = Depends(Provide[AuthContainer.services.user_service]),
):
    """Get user details (admin only)."""
    try:
        return await user_service.get_user(user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@admin_router.patch("/users/{user_id}")
@inject
async def update_user(
    user_id: str,
    update_data: UserUpdate,
    user_service: UserService = Depends(Provide[AuthContainer.services.user_service]),
):
    """Update user (admin only)."""
    try:
        return await user_service.update_user(user_id, update_data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@admin_router.delete("/users/{user_id}")
@inject
async def delete_user(
    user_id: str,
    user_service: UserService = Depends(Provide[AuthContainer.services.user_service]),
):
    """Delete user (admin only)."""
    try:
        await user_service.delete_user(user_id)
        return {"message": "User deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@admin_router.post("/users/{user_id}/activate")
@inject
async def activate_user(
    user_id: str,
    user_service: UserService = Depends(Provide[AuthContainer.services.user_service]),
):
    """Activate user account (admin only)."""
    await user_service.activate_user(user_id)
    return {"message": "User activated successfully"}


@admin_router.post("/users/{user_id}/deactivate")
@inject
async def deactivate_user(
    user_id: str,
    user_service: UserService = Depends(Provide[AuthContainer.services.user_service]),
):
    """Deactivate user account (admin only)."""
    await user_service.deactivate_user(user_id)
    return {"message": "User deactivated successfully"}


@admin_router.post("/users/{user_id}/assign-role")
@inject
async def assign_role(
    user_id: str,
    role: str,
    user_service: UserService = Depends(Provide[AuthContainer.services.user_service]),
):
    """Assign role to user (admin only)."""
    await user_service.assign_role(user_id, role)
    return {"message": f"Role '{role}' assigned to user successfully"}