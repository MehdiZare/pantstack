"""User domain model"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class UserRole(Enum):
    """User roles in the system"""

    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class UserStatus(Enum):
    """User account status"""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


@dataclass
class User:
    """User entity"""

    id: str
    email: str
    username: str
    hashed_password: str
    role: UserRole
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    email_verified: bool = False

    def is_active(self) -> bool:
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE

    def can_login(self) -> bool:
        """Check if user can login"""
        return self.is_active() and self.email_verified

    def has_role(self, role: UserRole) -> bool:
        """Check if user has a specific role"""
        return self.role == role

    def is_admin(self) -> bool:
        """Check if user is an admin"""
        return self.has_role(UserRole.ADMIN)
