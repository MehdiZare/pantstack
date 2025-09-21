"""Token repository interface"""
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime

from ..models import Token, TokenType


class TokenRepository(ABC):
    """Abstract interface for token persistence"""

    @abstractmethod
    async def create(
        self,
        user_id: str,
        token_type: TokenType,
        token: str,
        expires_at: Optional[datetime] = None,
        metadata: Optional[dict] = None
    ) -> Token:
        """Create a new token"""
        pass

    @abstractmethod
    async def find_by_id(self, token_id: str) -> Optional[Token]:
        """Find a token by ID"""
        pass

    @abstractmethod
    async def find_by_token(self, token_string: str) -> Optional[Token]:
        """Find a token by its token string"""
        pass

    @abstractmethod
    async def find_by_user(
        self,
        user_id: str,
        token_type: Optional[TokenType] = None
    ) -> List[Token]:
        """Find tokens by user ID and optionally type"""
        pass

    @abstractmethod
    async def revoke(self, token_id: str) -> bool:
        """Revoke a token"""
        pass

    @abstractmethod
    async def delete(self, token_id: str) -> bool:
        """Delete a token"""
        pass

    @abstractmethod
    async def delete_expired(self) -> int:
        """Delete all expired tokens"""
        pass