"""Service layer for user module."""

from typing import List, Optional

from stack.libs.shared.core.config import BaseConfig

from services.auth.lib.core.events import EventBackbone, EventType
from services.auth.lib.modules.users.repositories import UserRepository
from services.auth.lib.modules.users.schemas import (
    User,
    UserList,
    UserProfile,
    UserUpdate,
)


class UserService:
    """Service for user operations."""

    def __init__(
        self,
        user_repo: UserRepository,
        event_backbone: EventBackbone,
        config: BaseConfig,
    ):
        """Initialize user service.

        Args:
            user_repo: User repository
            event_backbone: Event publishing
            config: Service configuration
        """
        self.user_repo = user_repo
        self.event_backbone = event_backbone
        self.config = config

    async def get_profile(self, user_id: str) -> UserProfile:
        """Get user profile.

        Args:
            user_id: User ID

        Returns:
            User profile

        Raises:
            ValueError: If user not found
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise ValueError("User not found")

        return UserProfile(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login=user.last_login,
        )

    async def update_profile(
        self, user_id: str, update_data: UserUpdate
    ) -> UserProfile:
        """Update user profile.

        Args:
            user_id: User ID
            update_data: Update data

        Returns:
            Updated profile

        Raises:
            ValueError: If user not found
        """
        # Prevent role updates through profile endpoint
        update_data.role = None

        user = await self.user_repo.update(user_id, update_data)
        if not user:
            raise ValueError("User not found")

        await self.event_backbone.publish(
            EventType.USER_UPDATED,
            {"user_id": user_id, "changes": update_data.model_dump(exclude_unset=True)},
            user_id=user_id,
        )

        return UserProfile(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_verified=user.is_verified,
            created_at=user.created_at,
            last_login=user.last_login,
        )

    async def list_all_users(
        self, page: int = 1, page_size: int = 20, filter_active: Optional[bool] = None
    ) -> UserList:
        """List all users (admin only).

        Args:
            page: Page number
            page_size: Page size
            filter_active: Filter by active status

        Returns:
            User list
        """
        offset = (page - 1) * page_size
        users = await self.user_repo.list(offset, page_size, filter_active)
        total = await self.user_repo.count(filter_active)

        profiles = [
            UserProfile(
                id=user.id,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                role=user.role,
                is_verified=user.is_verified,
                created_at=user.created_at,
                last_login=user.last_login,
            )
            for user in users
        ]

        return UserList(
            users=profiles,
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_user(self, user_id: str) -> User:
        """Get full user details (admin only).

        Args:
            user_id: User ID

        Returns:
            User details

        Raises:
            ValueError: If user not found
        """
        user = await self.user_repo.get(user_id)
        if not user:
            raise ValueError("User not found")
        return user

    async def update_user(self, user_id: str, update_data: UserUpdate) -> User:
        """Update user (admin only).

        Args:
            user_id: User ID
            update_data: Update data

        Returns:
            Updated user

        Raises:
            ValueError: If user not found
        """
        user = await self.user_repo.update(user_id, update_data)
        if not user:
            raise ValueError("User not found")

        await self.event_backbone.publish(
            EventType.USER_UPDATED,
            {"user_id": user_id, "changes": update_data.model_dump(exclude_unset=True)},
            user_id=user_id,
        )

        return user

    async def delete_user(self, user_id: str) -> None:
        """Delete user (admin only).

        Args:
            user_id: User ID

        Raises:
            ValueError: If deletion failed
        """
        success = await self.user_repo.delete(user_id)
        if not success:
            raise ValueError("Failed to delete user")

        await self.event_backbone.publish(
            EventType.USER_DELETED,
            {"user_id": user_id},
            user_id=user_id,
        )

    async def activate_user(self, user_id: str) -> None:
        """Activate user account.

        Args:
            user_id: User ID
        """
        await self.user_repo.update(user_id, UserUpdate(is_active=True))

        await self.event_backbone.publish(
            EventType.USER_UPDATED,
            {"user_id": user_id, "changes": {"is_active": True}},
            user_id=user_id,
        )

    async def deactivate_user(self, user_id: str) -> None:
        """Deactivate user account.

        Args:
            user_id: User ID
        """
        await self.user_repo.update(user_id, UserUpdate(is_active=False))

        await self.event_backbone.publish(
            EventType.USER_UPDATED,
            {"user_id": user_id, "changes": {"is_active": False}},
            user_id=user_id,
        )

    async def assign_role(self, user_id: str, role: str) -> None:
        """Assign role to user.

        Args:
            user_id: User ID
            role: Role name
        """
        await self.user_repo.update(user_id, UserUpdate(role=role))

        await self.event_backbone.publish(
            EventType.ROLE_ASSIGNED,
            {"user_id": user_id, "role": role},
            user_id=user_id,
        )

    async def cleanup_inactive_users(self, days: int = 90) -> int:
        """Cleanup inactive users.

        Args:
            days: Days of inactivity

        Returns:
            Number of users cleaned up
        """
        inactive_users = await self.user_repo.get_inactive_users(days)

        count = 0
        for user in inactive_users:
            if not user.is_verified:
                # Delete unverified inactive users
                await self.delete_user(user.id)
                count += 1
            else:
                # Deactivate verified but inactive users
                await self.deactivate_user(user.id)
                count += 1

        return count

    async def send_welcome_email(self, user_id: str) -> None:
        """Send welcome email to user.

        Args:
            user_id: User ID
        """
        user = await self.user_repo.get(user_id)
        if not user:
            return

        # This would integrate with email service
        # For now, just log
        print(f"📧 Sending welcome email to {user.email}")

    async def send_verification_email(self, user_id: str, token: str) -> None:
        """Send verification email.

        Args:
            user_id: User ID
            token: Verification token
        """
        user = await self.user_repo.get(user_id)
        if not user:
            return

        # This would integrate with email service
        verification_url = f"{self.config.api_prefix}/auth/verify?token={token}"
        print(f"📧 Sending verification email to {user.email}: {verification_url}")

    async def send_password_reset_email(self, email: str, token: str) -> None:
        """Send password reset email.

        Args:
            email: User email
            token: Reset token
        """
        # This would integrate with email service
        reset_url = f"{self.config.api_prefix}/auth/reset-password?token={token}"
        print(f"📧 Sending password reset email to {email}: {reset_url}")