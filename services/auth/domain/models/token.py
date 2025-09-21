"""Token domain model"""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional


class TokenType(Enum):
    """Types of tokens"""
    ACCESS = "access"
    REFRESH = "refresh"
    VERIFICATION = "verification"
    PASSWORD_RESET = "password_reset"


@dataclass
class Token:
    """Token entity"""
    id: str
    user_id: str
    token_type: TokenType
    token: str
    expires_at: datetime
    created_at: datetime
    revoked: bool = False
    metadata: Optional[Dict[str, Any]] = None

    def is_expired(self) -> bool:
        """Check if token is expired"""
        return datetime.utcnow() >= self.expires_at

    def is_valid(self) -> bool:
        """Check if token is valid"""
        return not self.revoked and not self.is_expired()

    def revoke(self):
        """Revoke the token"""
        self.revoked = True