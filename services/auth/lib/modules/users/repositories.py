"""Repository layer for user module."""

from datetime import datetime
from typing import List, Optional

from services.auth.lib.core.database import SupabaseClient
from services.auth.lib.modules.users.schemas import User, UserCreate, UserUpdate


class UserRepository:
    """Repository for user data."""

    def __init__(self, db: SupabaseClient):
        """Initialize user repository.

        Args:
            db: Database client
        """
        self.db = db
        self.table_name = "users"

    async def create(self, user_data: UserCreate) -> User:
        """Create a new user.

        Args:
            user_data: User creation data

        Returns:
            Created user
        """
        data = user_data.model_dump()
        data["created_at"] = datetime.utcnow().isoformat()
        data["updated_at"] = datetime.utcnow().isoformat()

        # Mock implementation for development
        if not self.db.client:
            # Generate mock ID
            data["id"] = f"user_{datetime.utcnow().timestamp()}"
            return User(**data)

        response = self.db.table(self.table_name).insert(data).execute()

        if response.error:
            raise ValueError(f"Failed to create user: {response.error}")

        return User(**response.data[0])

    async def get(self, user_id: str) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User if found
        """
        # Mock implementation for development
        if not self.db.client:
            return None

        response = self.db.table(self.table_name).select("*").eq("id", user_id).single().execute()

        if response.error or not response.data:
            return None

        return User(**response.data)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email.

        Args:
            email: User email

        Returns:
            User if found
        """
        # Mock implementation for development
        if not self.db.client:
            return None

        response = (
            self.db.table(self.table_name).select("*").eq("email", email).single().execute()
        )

        if response.error or not response.data:
            return None

        return User(**response.data)

    async def update(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user.

        Args:
            user_id: User ID
            user_data: Update data

        Returns:
            Updated user
        """
        data = user_data.model_dump(exclude_unset=True)
        if not data:
            return await self.get(user_id)

        data["updated_at"] = datetime.utcnow().isoformat()

        # Mock implementation for development
        if not self.db.client:
            return None

        response = self.db.table(self.table_name).update(data).eq("id", user_id).execute()

        if response.error:
            raise ValueError(f"Failed to update user: {response.error}")

        if not response.data:
            return None

        return User(**response.data[0])

    async def delete(self, user_id: str) -> bool:
        """Delete user.

        Args:
            user_id: User ID

        Returns:
            True if deleted
        """
        # Mock implementation for development
        if not self.db.client:
            return True

        response = self.db.table(self.table_name).delete().eq("id", user_id).execute()

        return response.error is None

    async def list(
        self, offset: int = 0, limit: int = 20, filter_active: Optional[bool] = None
    ) -> List[User]:
        """List users.

        Args:
            offset: Pagination offset
            limit: Pagination limit
            filter_active: Filter by active status

        Returns:
            List of users
        """
        # Mock implementation for development
        if not self.db.client:
            return []

        query = self.db.table(self.table_name).select("*")

        if filter_active is not None:
            query = query.eq("is_active", filter_active)

        response = query.range(offset, offset + limit - 1).execute()

        if response.error:
            raise ValueError(f"Failed to list users: {response.error}")

        return [User(**item) for item in response.data]

    async def count(self, filter_active: Optional[bool] = None) -> int:
        """Count users.

        Args:
            filter_active: Filter by active status

        Returns:
            User count
        """
        # Mock implementation for development
        if not self.db.client:
            return 0

        query = self.db.table(self.table_name).select("id", count="exact")

        if filter_active is not None:
            query = query.eq("is_active", filter_active)

        response = query.execute()

        if response.error:
            raise ValueError(f"Failed to count users: {response.error}")

        return response.count or 0

    async def update_password(self, user_id: str, password_hash: str) -> bool:
        """Update user password.

        Args:
            user_id: User ID
            password_hash: New password hash

        Returns:
            True if updated
        """
        data = {
            "password_hash": password_hash,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Mock implementation for development
        if not self.db.client:
            return True

        response = self.db.table(self.table_name).update(data).eq("id", user_id).execute()

        return response.error is None

    async def update_last_login(self, user_id: str) -> bool:
        """Update user's last login time.

        Args:
            user_id: User ID

        Returns:
            True if updated
        """
        data = {"last_login": datetime.utcnow().isoformat()}

        # Mock implementation for development
        if not self.db.client:
            return True

        response = self.db.table(self.table_name).update(data).eq("id", user_id).execute()

        return response.error is None

    async def mark_verified(self, user_id: str) -> bool:
        """Mark user as verified.

        Args:
            user_id: User ID

        Returns:
            True if updated
        """
        data = {
            "is_verified": True,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Mock implementation for development
        if not self.db.client:
            return True

        response = self.db.table(self.table_name).update(data).eq("id", user_id).execute()

        return response.error is None

    async def get_inactive_users(self, days: int = 90) -> List[User]:
        """Get inactive users.

        Args:
            days: Days of inactivity

        Returns:
            List of inactive users
        """
        # Mock implementation for development
        if not self.db.client:
            return []

        from datetime import timedelta

        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()

        response = (
            self.db.table(self.table_name)
            .select("*")
            .or_(f"last_login.lt.{cutoff_date},last_login.is.null")
            .execute()
        )

        if response.error:
            raise ValueError(f"Failed to get inactive users: {response.error}")

        return [User(**item) for item in response.data]