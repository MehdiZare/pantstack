"""In-memory implementation of user repository for development/testing"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from ...domain.models import User, UserRole, UserStatus
from ...domain.ports import UserRepository


class InMemoryUserRepository(UserRepository):
    """In-memory user repository implementation"""

    def __init__(self):
        self.users: Dict[str, User] = {}
        self.email_index: Dict[str, str] = {}  # email -> user_id
        self.username_index: Dict[str, str] = {}  # username -> user_id

    async def create(self, email: str, username: str, hashed_password: str) -> User:
        """Create a new user"""
        user_id = str(uuid.uuid4())
        now = datetime.utcnow()

        user = User(
            id=user_id,
            email=email,
            username=username,
            hashed_password=hashed_password,
            role=UserRole.USER,
            status=UserStatus.PENDING_VERIFICATION,
            created_at=now,
            updated_at=now,
            email_verified=False,
        )

        self.users[user_id] = user
        self.email_index[email] = user_id
        self.username_index[username] = user_id

        return user

    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Find a user by ID"""
        return self.users.get(user_id)

    async def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email"""
        user_id = self.email_index.get(email)
        if user_id:
            return self.users.get(user_id)
        return None

    async def find_by_username(self, username: str) -> Optional[User]:
        """Find a user by username"""
        user_id = self.username_index.get(username)
        if user_id:
            return self.users.get(user_id)
        return None

    async def update(self, user: User) -> User:
        """Update a user"""
        if user.id not in self.users:
            raise ValueError(f"User {user.id} not found")

        # Update indexes if email or username changed
        old_user = self.users[user.id]
        if old_user.email != user.email:
            del self.email_index[old_user.email]
            self.email_index[user.email] = user.id

        if old_user.username != user.username:
            del self.username_index[old_user.username]
            self.username_index[user.username] = user.id

        user.updated_at = datetime.utcnow()
        self.users[user.id] = user
        return user

    async def delete(self, user_id: str) -> bool:
        """Delete a user"""
        if user_id not in self.users:
            return False

        user = self.users[user_id]
        del self.email_index[user.email]
        del self.username_index[user.username]
        del self.users[user_id]
        return True

    async def list(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List users with pagination"""
        all_users = list(self.users.values())
        return all_users[offset : offset + limit]

    async def exists(self, email: str) -> bool:
        """Check if a user exists by email"""
        return email in self.email_index
