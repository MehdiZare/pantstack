"""Repository layer for auth module."""

import json
from datetime import datetime, timedelta
from typing import Optional

import redis

from services.auth.lib.core.database import SupabaseClient


class AuthRepository:
    """Repository for authentication data."""

    def __init__(self, db: SupabaseClient, redis: redis.Redis):
        """Initialize auth repository.

        Args:
            db: Database client
            redis: Redis client
        """
        self.db = db
        self.redis = redis

    async def store_refresh_token(
        self, user_id: str, token: str, expires_in: int
    ) -> None:
        """Store refresh token in Redis.

        Args:
            user_id: User ID
            token: Refresh token
            expires_in: Expiration time in seconds
        """
        key = f"refresh_token:{token}"
        self.redis.setex(key, expires_in, user_id)

        # Also track active tokens for user
        user_tokens_key = f"user_tokens:{user_id}"
        self.redis.sadd(user_tokens_key, token)
        self.redis.expire(user_tokens_key, expires_in)

    async def validate_refresh_token(self, token: str) -> Optional[str]:
        """Validate refresh token and return user ID.

        Args:
            token: Refresh token

        Returns:
            User ID if valid, None otherwise
        """
        key = f"refresh_token:{token}"
        user_id = self.redis.get(key)
        return user_id

    async def revoke_refresh_token(self, token: str) -> None:
        """Revoke a refresh token.

        Args:
            token: Refresh token to revoke
        """
        key = f"refresh_token:{token}"
        user_id = self.redis.get(key)

        if user_id:
            # Remove from user's active tokens
            user_tokens_key = f"user_tokens:{user_id}"
            self.redis.srem(user_tokens_key, token)

        # Delete the token
        self.redis.delete(key)

    async def revoke_all_user_tokens(self, user_id: str) -> None:
        """Revoke all refresh tokens for a user.

        Args:
            user_id: User ID
        """
        user_tokens_key = f"user_tokens:{user_id}"
        tokens = self.redis.smembers(user_tokens_key)

        for token in tokens:
            key = f"refresh_token:{token}"
            self.redis.delete(key)

        self.redis.delete(user_tokens_key)

    async def track_login_attempt(self, email: str) -> int:
        """Track login attempt for rate limiting.

        Args:
            email: User email

        Returns:
            Number of attempts
        """
        key = f"login_attempts:{email}"
        attempts = self.redis.incr(key)

        # Set expiry for 15 minutes if first attempt
        if attempts == 1:
            self.redis.expire(key, 900)  # 15 minutes

        return attempts

    async def reset_login_attempts(self, email: str) -> None:
        """Reset login attempts for an email.

        Args:
            email: User email
        """
        key = f"login_attempts:{email}"
        self.redis.delete(key)

    async def is_account_locked(self, email: str) -> bool:
        """Check if account is locked due to failed attempts.

        Args:
            email: User email

        Returns:
            True if locked
        """
        key = f"account_locked:{email}"
        return bool(self.redis.exists(key))

    async def lock_account(self, email: str, duration: int = 900) -> None:
        """Lock account for specified duration.

        Args:
            email: User email
            duration: Lock duration in seconds (default 15 minutes)
        """
        key = f"account_locked:{email}"
        self.redis.setex(key, duration, "locked")

    async def unlock_account(self, email: str) -> None:
        """Unlock an account.

        Args:
            email: User email
        """
        key = f"account_locked:{email}"
        self.redis.delete(key)

    async def store_password_reset_token(
        self, email: str, token: str, expires_in: int = 3600
    ) -> None:
        """Store password reset token.

        Args:
            email: User email
            token: Reset token
            expires_in: Expiration in seconds (default 1 hour)
        """
        key = f"password_reset:{token}"
        self.redis.setex(key, expires_in, email)

    async def validate_password_reset_token(self, token: str) -> Optional[str]:
        """Validate password reset token.

        Args:
            token: Reset token

        Returns:
            Email if valid, None otherwise
        """
        key = f"password_reset:{token}"
        email = self.redis.get(key)
        return email

    async def delete_password_reset_token(self, token: str) -> None:
        """Delete password reset token after use.

        Args:
            token: Reset token
        """
        key = f"password_reset:{token}"
        self.redis.delete(key)

    async def store_email_verification_token(
        self, email: str, token: str, expires_in: int = 86400
    ) -> None:
        """Store email verification token.

        Args:
            email: User email
            token: Verification token
            expires_in: Expiration in seconds (default 24 hours)
        """
        key = f"email_verify:{token}"
        self.redis.setex(key, expires_in, email)

    async def validate_email_verification_token(self, token: str) -> Optional[str]:
        """Validate email verification token.

        Args:
            token: Verification token

        Returns:
            Email if valid, None otherwise
        """
        key = f"email_verify:{token}"
        email = self.redis.get(key)
        return email

    async def delete_email_verification_token(self, token: str) -> None:
        """Delete email verification token after use.

        Args:
            token: Verification token
        """
        key = f"email_verify:{token}"
        self.redis.delete(key)

    async def store_session(
        self, session_id: str, user_id: str, data: dict, expires_in: int = 3600
    ) -> None:
        """Store user session.

        Args:
            session_id: Session ID
            user_id: User ID
            data: Session data
            expires_in: Expiration in seconds
        """
        key = f"session:{session_id}"
        session_data = {
            "user_id": user_id,
            **data,
            "created_at": datetime.utcnow().isoformat(),
        }
        self.redis.setex(key, expires_in, json.dumps(session_data))

        # Track user sessions
        user_sessions_key = f"user_sessions:{user_id}"
        self.redis.sadd(user_sessions_key, session_id)
        self.redis.expire(user_sessions_key, expires_in)

    async def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data.

        Args:
            session_id: Session ID

        Returns:
            Session data if exists
        """
        key = f"session:{session_id}"
        data = self.redis.get(key)
        return json.loads(data) if data else None

    async def delete_session(self, session_id: str) -> None:
        """Delete a session.

        Args:
            session_id: Session ID
        """
        key = f"session:{session_id}"
        data = self.redis.get(key)

        if data:
            session_data = json.loads(data)
            user_id = session_data.get("user_id")

            if user_id:
                user_sessions_key = f"user_sessions:{user_id}"
                self.redis.srem(user_sessions_key, session_id)

        self.redis.delete(key)
