"""User-related Celery tasks."""

from celery import shared_task
from dependency_injector.wiring import Provide, inject

from services.auth.lib.core.container import AuthContainer, get_container
from services.auth.lib.modules.users import UserService


@shared_task(name="auth.send_welcome_email")
@inject
def send_welcome_email(
    user_id: str,
    user_service: UserService = Provide[AuthContainer.services.user_service],
) -> dict:
    """Send welcome email to new user.

    Args:
        user_id: User ID

    Returns:
        Task result
    """
    # Get container and wire if needed
    container = get_container()

    try:
        user_service = container.services.user_service()
        user_service.send_welcome_email(user_id)
        return {"status": "success", "user_id": user_id, "task": "welcome_email"}
    except Exception as e:
        return {"status": "error", "user_id": user_id, "error": str(e)}


@shared_task(name="auth.send_verification_email")
def send_verification_email(user_id: str, verification_token: str) -> dict:
    """Send email verification link.

    Args:
        user_id: User ID
        verification_token: Email verification token

    Returns:
        Task result
    """
    container = get_container()

    try:
        user_service = container.services.user_service()
        user_service.send_verification_email(user_id, verification_token)
        return {
            "status": "success",
            "user_id": user_id,
            "task": "verification_email",
        }
    except Exception as e:
        return {"status": "error", "user_id": user_id, "error": str(e)}


@shared_task(name="auth.send_password_reset_email")
def send_password_reset_email(email: str, reset_token: str) -> dict:
    """Send password reset email.

    Args:
        email: User email
        reset_token: Password reset token

    Returns:
        Task result
    """
    container = get_container()

    try:
        user_service = container.services.user_service()
        user_service.send_password_reset_email(email, reset_token)
        return {"status": "success", "email": email, "task": "password_reset_email"}
    except Exception as e:
        return {"status": "error", "email": email, "error": str(e)}


@shared_task(name="auth.cleanup_inactive_users")
def cleanup_inactive_users(days: int = 90) -> dict:
    """Clean up inactive users.

    Args:
        days: Days of inactivity threshold

    Returns:
        Task result with count of cleaned users
    """
    container = get_container()

    try:
        user_service = container.services.user_service()
        count = user_service.cleanup_inactive_users(days)
        return {
            "status": "success",
            "task": "cleanup_inactive_users",
            "cleaned_count": count,
            "days_threshold": days,
        }
    except Exception as e:
        return {"status": "error", "task": "cleanup_inactive_users", "error": str(e)}


@shared_task(name="auth.sync_user_data")
def sync_user_data(user_id: str) -> dict:
    """Sync user data with external systems.

    Args:
        user_id: User ID

    Returns:
        Task result
    """
    container = get_container()

    try:
        # This would sync with external systems
        # For now, just a placeholder
        print(f"Syncing user data for user_id: {user_id}")
        return {"status": "success", "user_id": user_id, "task": "sync_user_data"}
    except Exception as e:
        return {"status": "error", "user_id": user_id, "error": str(e)}


@shared_task(name="auth.deactivate_expired_accounts")
def deactivate_expired_accounts() -> dict:
    """Deactivate accounts that have expired.

    Returns:
        Task result with count of deactivated accounts
    """
    container = get_container()

    try:
        user_service = container.services.user_service()
        # Get users who haven't logged in for 180 days
        inactive_users = user_service.user_repo.get_inactive_users(180)

        deactivated_count = 0
        for user in inactive_users:
            if user.is_active:
                user_service.deactivate_user(user.id)
                deactivated_count += 1

        return {
            "status": "success",
            "task": "deactivate_expired_accounts",
            "deactivated_count": deactivated_count,
        }
    except Exception as e:
        return {
            "status": "error",
            "task": "deactivate_expired_accounts",
            "error": str(e),
        }