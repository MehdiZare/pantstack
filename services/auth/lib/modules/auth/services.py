"""Service layer for auth module."""

import secrets
from datetime import datetime, timedelta
from typing import Optional

from services.auth.lib.core.events import EventBackbone, EventType
from services.auth.lib.modules.auth.repositories import AuthRepository
from services.auth.lib.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    TokenResponse,
)
from services.auth.lib.modules.users.repositories import UserRepository
from services.auth.lib.modules.users.schemas import User, UserCreate
from stack.libs.shared.core.config import BaseConfig
from stack.libs.shared.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)


class AuthService:
    """Service for authentication operations."""

    def __init__(
        self,
        auth_repo: AuthRepository,
        user_repo: UserRepository,
        event_backbone: EventBackbone,
        config: BaseConfig,
    ):
        """Initialize auth service.

        Args:
            auth_repo: Auth repository
            user_repo: User repository
            event_backbone: Event publishing
            config: Service configuration
        """
        self.auth_repo = auth_repo
        self.user_repo = user_repo
        self.event_backbone = event_backbone
        self.config = config

    async def register(self, request: RegisterRequest) -> LoginResponse:
        """Register a new user.

        Args:
            request: Registration request

        Returns:
            Login response with tokens

        Raises:
            ValueError: If user already exists
        """
        # Check if user exists
        existing = await self.user_repo.get_by_email(request.email)
        if existing:
            raise ValueError("User with this email already exists")

        # Create user
        user_data = UserCreate(
            email=request.email,
            password_hash=get_password_hash(request.password),
            first_name=request.first_name,
            last_name=request.last_name,
            is_verified=False,
            is_active=True,
        )

        user = await self.user_repo.create(user_data)

        # Generate tokens
        tokens = await self._generate_tokens(user)

        # Send verification email
        if self.config.auth_module.require_email_verification:
            verification_token = secrets.token_urlsafe(32)
            await self.auth_repo.store_email_verification_token(
                user.email, verification_token
            )

            # Queue email task
            await self.event_backbone.publish(
                EventType.USER_REGISTERED,
                {
                    "user_id": user.id,
                    "email": user.email,
                    "verification_token": verification_token,
                },
                user_id=user.id,
            )

        return LoginResponse(
            user_id=user.id,
            email=user.email,
            tokens=tokens,
            is_verified=user.is_verified,
            last_login=None,
        )

    async def login(self, request: LoginRequest) -> LoginResponse:
        """Login a user.

        Args:
            request: Login request

        Returns:
            Login response with tokens

        Raises:
            ValueError: If credentials invalid or account locked
        """
        # Check if account is locked
        if await self.auth_repo.is_account_locked(request.email):
            raise ValueError("Account is locked due to too many failed attempts")

        # Get user
        user = await self.user_repo.get_by_email(request.email)

        if not user or not verify_password(request.password, user.password_hash):
            # Track failed attempt
            attempts = await self.auth_repo.track_login_attempt(request.email)

            if attempts >= self.config.auth_module.max_login_attempts:
                await self.auth_repo.lock_account(
                    request.email,
                    self.config.auth_module.lockout_duration_minutes * 60,
                )
                await self.event_backbone.publish(
                    EventType.ACCOUNT_LOCKED,
                    {"email": request.email, "attempts": attempts},
                )
                raise ValueError("Account locked due to too many failed attempts")

            await self.event_backbone.publish(
                EventType.LOGIN_FAILED,
                {"email": request.email, "attempts": attempts},
            )
            raise ValueError("Invalid email or password")

        # Reset login attempts on successful login
        await self.auth_repo.reset_login_attempts(request.email)

        # Check if user is active
        if not user.is_active:
            raise ValueError("Account is inactive")

        # Generate tokens
        tokens = await self._generate_tokens(user)

        # Update last login
        await self.user_repo.update_last_login(user.id)

        # Publish login event
        await self.event_backbone.publish(
            EventType.USER_LOGIN,
            {"user_id": user.id, "email": user.email},
            user_id=user.id,
        )

        return LoginResponse(
            user_id=user.id,
            email=user.email,
            tokens=tokens,
            is_verified=user.is_verified,
            last_login=datetime.utcnow(),
        )

    async def logout(self, user_id: str, token: str) -> None:
        """Logout a user.

        Args:
            user_id: User ID
            token: Refresh token to revoke
        """
        await self.auth_repo.revoke_refresh_token(token)

        await self.event_backbone.publish(
            EventType.USER_LOGOUT, {"user_id": user_id}, user_id=user_id
        )

    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token.

        Args:
            refresh_token: Refresh token

        Returns:
            New token response

        Raises:
            ValueError: If refresh token invalid
        """
        # Validate refresh token
        user_id = await self.auth_repo.validate_refresh_token(refresh_token)
        if not user_id:
            raise ValueError("Invalid refresh token")

        # Get user
        user = await self.user_repo.get(user_id)
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")

        # Generate new access token
        access_token = create_access_token(user.id, user.email, user.role, self.config)

        await self.event_backbone.publish(
            EventType.TOKEN_REFRESHED, {"user_id": user_id}, user_id=user_id
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,  # Keep same refresh token
            expires_in=self.config.auth_module.access_token_expire_minutes * 60,
        )

    async def change_password(
        self, user_id: str, current_password: str, new_password: str
    ) -> None:
        """Change user password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Raises:
            ValueError: If current password invalid
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise ValueError("User not found")

        if not verify_password(current_password, user.password_hash):
            raise ValueError("Current password is incorrect")

        # Update password
        new_hash = get_password_hash(new_password)
        await self.user_repo.update_password(user_id, new_hash)

        # Revoke all existing tokens
        await self.auth_repo.revoke_all_user_tokens(user_id)

        await self.event_backbone.publish(
            EventType.USER_PASSWORD_CHANGED, {"user_id": user_id}, user_id=user_id
        )

    async def request_password_reset(self, email: str) -> None:
        """Request password reset.

        Args:
            email: User email
        """
        user = await self.user_repo.get_by_email(email)
        if user:  # Don't reveal if user exists
            reset_token = secrets.token_urlsafe(32)
            await self.auth_repo.store_password_reset_token(email, reset_token)

            await self.event_backbone.publish(
                EventType.USER_PASSWORD_RESET,
                {"user_id": user.id, "email": email, "reset_token": reset_token},
                user_id=user.id,
            )

    async def reset_password(self, token: str, new_password: str) -> None:
        """Reset password with token.

        Args:
            token: Reset token
            new_password: New password

        Raises:
            ValueError: If token invalid
        """
        email = await self.auth_repo.validate_password_reset_token(token)
        if not email:
            raise ValueError("Invalid or expired reset token")

        user = await self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("User not found")

        # Update password
        new_hash = get_password_hash(new_password)
        await self.user_repo.update_password(user.id, new_hash)

        # Delete reset token
        await self.auth_repo.delete_password_reset_token(token)

        # Revoke all existing tokens
        await self.auth_repo.revoke_all_user_tokens(user.id)

        await self.event_backbone.publish(
            EventType.USER_PASSWORD_CHANGED, {"user_id": user.id}, user_id=user.id
        )

    async def verify_email(self, token: str) -> None:
        """Verify email with token.

        Args:
            token: Verification token

        Raises:
            ValueError: If token invalid
        """
        email = await self.auth_repo.validate_email_verification_token(token)
        if not email:
            raise ValueError("Invalid or expired verification token")

        user = await self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("User not found")

        # Mark as verified
        await self.user_repo.mark_verified(user.id)

        # Delete verification token
        await self.auth_repo.delete_email_verification_token(token)

        await self.event_backbone.publish(
            EventType.USER_VERIFIED, {"user_id": user.id}, user_id=user.id
        )

    async def _generate_tokens(self, user: User) -> TokenResponse:
        """Generate access and refresh tokens.

        Args:
            user: User object

        Returns:
            Token response
        """
        # Generate access token
        access_token = create_access_token(user.id, user.email, user.role, self.config)

        # Generate refresh token
        refresh_token = secrets.token_urlsafe(32)
        refresh_expires = self.config.auth_module.refresh_token_expire_days * 86400

        # Store refresh token
        await self.auth_repo.store_refresh_token(
            user.id, refresh_token, refresh_expires
        )

        await self.event_backbone.publish(
            EventType.TOKEN_GENERATED, {"user_id": user.id}, user_id=user.id
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.config.auth_module.access_token_expire_minutes * 60,
        )

    async def verify_token(self, token: str) -> "TokenVerifyResponse":
        """Verify a JWT token.

        Args:
            token: JWT token to verify

        Returns:
            Token verification response

        Raises:
            ValueError: If token is invalid
        """
        from datetime import datetime

        from services.auth.lib.modules.auth.schemas import TokenVerifyResponse
        from stack.libs.shared.core.security import decode_access_token

        try:
            # Decode the token
            payload = decode_access_token(
                token, self.config.jwt_secret_key, self.config.jwt_algorithm
            )

            # Check if token is blacklisted
            if await self.auth_repo.is_token_blacklisted(token):
                raise ValueError("Token has been revoked")

            return TokenVerifyResponse(
                valid=True,
                user_id=payload.get("sub"),
                email=payload.get("email"),
                expires_at=datetime.fromtimestamp(payload.get("exp", 0)),
            )
        except Exception:
            return TokenVerifyResponse(
                valid=False, user_id=None, email=None, expires_at=None
            )
