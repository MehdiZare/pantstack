"""Auth service configuration."""

from typing import Optional

from pydantic import Field

from stack.libs.shared.core.config import (
    AWSConfig,
    BaseConfig,
    CeleryConfig,
    DatabaseConfig,
    RedisConfig,
)


class AuthModuleConfig(BaseConfig):
    """Auth module specific configuration."""

    # Token settings
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration"
    )
    refresh_token_expire_days: int = Field(
        default=7, description="Refresh token expiration"
    )

    # Password policy
    min_password_length: int = Field(default=8, description="Minimum password length")
    require_uppercase: bool = Field(
        default=True, description="Require uppercase letter"
    )
    require_lowercase: bool = Field(
        default=True, description="Require lowercase letter"
    )
    require_digit: bool = Field(default=True, description="Require digit")
    require_special: bool = Field(
        default=False, description="Require special character"
    )

    # Rate limiting
    max_login_attempts: int = Field(default=5, description="Max login attempts")
    lockout_duration_minutes: int = Field(
        default=15, description="Account lockout duration"
    )

    # User settings
    require_email_verification: bool = Field(
        default=True, description="Require email verification"
    )
    allow_registration: bool = Field(
        default=True, description="Allow new user registration"
    )
    default_user_role: str = Field(
        default="user", description="Default role for new users"
    )

    # Session settings
    session_timeout_minutes: int = Field(default=60, description="Session timeout")
    allow_multiple_sessions: bool = Field(
        default=True, description="Allow multiple active sessions"
    )


class AuthConfig(BaseConfig):
    """Complete auth service configuration."""

    service_name: str = Field(default="auth", description="Service name")

    # Module configurations
    auth_module: AuthModuleConfig = Field(default_factory=AuthModuleConfig)

    # Infrastructure configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    celery: CeleryConfig = Field(default_factory=CeleryConfig)
    aws: AWSConfig = Field(default_factory=AWSConfig)

    # Service-specific settings
    enable_oauth: bool = Field(default=False, description="Enable OAuth providers")
    oauth_providers: list[str] = Field(
        default_factory=list, description="OAuth provider list"
    )

    @classmethod
    def from_environment(cls) -> "AuthConfig":
        """Load configuration based on environment."""
        config = super().from_environment()

        # Override with auth-specific settings
        config.service_name = "auth"

        # Set Celery task routing for auth service
        config.celery.task_routes.update(
            {
                "auth.*": {"queue": "auth"},
                "users.*": {"queue": "auth"},
            }
        )

        return config
