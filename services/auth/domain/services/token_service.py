"""Token management domain service"""
from typing import Optional, List
from datetime import datetime, timedelta
import secrets

from ..models import Token, TokenType
from ..ports import TokenRepository


class TokenService:
    """Handles token management business logic"""

    # Token expiration times
    TOKEN_EXPIRY = {
        TokenType.ACCESS: timedelta(hours=1),
        TokenType.REFRESH: timedelta(days=30),
        TokenType.VERIFICATION: timedelta(days=7),
        TokenType.PASSWORD_RESET: timedelta(hours=24),
    }

    def __init__(self, token_repo: TokenRepository):
        self.token_repo = token_repo

    async def create_token(
        self,
        user_id: str,
        token_type: TokenType,
        metadata: Optional[dict] = None
    ) -> Token:
        """Create a new token"""
        token_string = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + self.TOKEN_EXPIRY[token_type]

        token = await self.token_repo.create(
            user_id=user_id,
            token_type=token_type,
            token=token_string,
            expires_at=expires_at,
            metadata=metadata
        )
        return token

    async def verify_token(self, token_string: str) -> Optional[Token]:
        """Verify a token"""
        token = await self.token_repo.find_by_token(token_string)

        if not token or not token.is_valid():
            return None

        return token

    async def revoke_token(self, token_id: str) -> bool:
        """Revoke a token"""
        return await self.token_repo.revoke(token_id)

    async def revoke_user_tokens(self, user_id: str, token_type: Optional[TokenType] = None) -> int:
        """Revoke all tokens for a user, optionally filtered by type"""
        tokens = await self.token_repo.find_by_user(user_id, token_type)
        count = 0
        for token in tokens:
            if await self.token_repo.revoke(token.id):
                count += 1
        return count

    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens"""
        return await self.token_repo.delete_expired()

    async def get_user_tokens(
        self,
        user_id: str,
        token_type: Optional[TokenType] = None
    ) -> List[Token]:
        """Get all tokens for a user"""
        return await self.token_repo.find_by_user(user_id, token_type)