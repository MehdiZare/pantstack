"""User management domain service"""
from typing import Optional, List
from datetime import datetime

from ..models import User, UserRole, UserStatus
from ..ports import UserRepository


class UserService:
    """Handles user management business logic"""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        return await self.user_repo.find_by_id(user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email"""
        return await self.user_repo.find_by_email(email)

    async def update_user(self, user_id: str, **kwargs) -> Optional[User]:
        """Update user information"""
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            return None

        # Update allowed fields
        allowed_fields = ["username", "email", "role", "status"]
        for field, value in kwargs.items():
            if field in allowed_fields and value is not None:
                setattr(user, field, value)

        user.updated_at = datetime.utcnow()
        return await self.user_repo.update(user)

    async def activate_user(self, user_id: str) -> Optional[User]:
        """Activate a user account"""
        return await self.update_user(
            user_id,
            status=UserStatus.ACTIVE,
            email_verified=True
        )

    async def suspend_user(self, user_id: str) -> Optional[User]:
        """Suspend a user account"""
        return await self.update_user(user_id, status=UserStatus.SUSPENDED)

    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        return await self.user_repo.delete(user_id)

    async def list_users(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List users with pagination"""
        return await self.user_repo.list(limit=limit, offset=offset)

    async def change_role(self, user_id: str, new_role: UserRole) -> Optional[User]:
        """Change a user's role"""
        return await self.update_user(user_id, role=new_role)

    async def record_login(self, user_id: str) -> Optional[User]:
        """Record a successful login"""
        user = await self.user_repo.find_by_id(user_id)
        if not user:
            return None

        user.last_login = datetime.utcnow()
        return await self.user_repo.update(user)