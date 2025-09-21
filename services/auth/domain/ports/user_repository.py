"""User repository interface"""
from abc import ABC, abstractmethod
from typing import Optional, List

from ..models import User


class UserRepository(ABC):
    """Abstract interface for user persistence"""

    @abstractmethod
    async def create(self, email: str, username: str, hashed_password: str) -> User:
        """Create a new user"""
        pass

    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Find a user by ID"""
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find a user by email"""
        pass

    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[User]:
        """Find a user by username"""
        pass

    @abstractmethod
    async def update(self, user: User) -> User:
        """Update a user"""
        pass

    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """Delete a user"""
        pass

    @abstractmethod
    async def list(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List users with pagination"""
        pass

    @abstractmethod
    async def exists(self, email: str) -> bool:
        """Check if a user exists by email"""
        pass