"""In-memory implementation of token repository for development/testing"""
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import uuid

from ...domain.models import Token, TokenType
from ...domain.ports import TokenRepository


class InMemoryTokenRepository(TokenRepository):
    """In-memory token repository implementation"""

    def __init__(self):
        self.tokens: Dict[str, Token] = {}
        self.token_index: Dict[str, str] = {}  # token_string -> token_id
        self.user_tokens: Dict[str, List[str]] = {}  # user_id -> [token_ids]

    async def create(
        self,
        user_id: str,
        token_type: TokenType,
        token: str,
        expires_at: Optional[datetime] = None,
        metadata: Optional[dict] = None
    ) -> Token:
        """Create a new token"""
        token_id = str(uuid.uuid4())
        now = datetime.utcnow()

        if expires_at is None:
            # Default expiration times
            expiry_deltas = {
                TokenType.ACCESS: timedelta(hours=1),
                TokenType.REFRESH: timedelta(days=30),
                TokenType.VERIFICATION: timedelta(days=7),
                TokenType.PASSWORD_RESET: timedelta(hours=24),
            }
            expires_at = now + expiry_deltas[token_type]

        token_obj = Token(
            id=token_id,
            user_id=user_id,
            token_type=token_type,
            token=token,
            expires_at=expires_at,
            created_at=now,
            revoked=False,
            metadata=metadata
        )

        self.tokens[token_id] = token_obj
        self.token_index[token] = token_id

        if user_id not in self.user_tokens:
            self.user_tokens[user_id] = []
        self.user_tokens[user_id].append(token_id)

        return token_obj

    async def find_by_id(self, token_id: str) -> Optional[Token]:
        """Find a token by ID"""
        return self.tokens.get(token_id)

    async def find_by_token(self, token_string: str) -> Optional[Token]:
        """Find a token by its token string"""
        token_id = self.token_index.get(token_string)
        if token_id:
            return self.tokens.get(token_id)
        return None

    async def find_by_user(
        self,
        user_id: str,
        token_type: Optional[TokenType] = None
    ) -> List[Token]:
        """Find tokens by user ID and optionally type"""
        token_ids = self.user_tokens.get(user_id, [])
        tokens = [self.tokens[tid] for tid in token_ids if tid in self.tokens]

        if token_type:
            tokens = [t for t in tokens if t.token_type == token_type]

        return tokens

    async def revoke(self, token_id: str) -> bool:
        """Revoke a token"""
        if token_id not in self.tokens:
            return False

        self.tokens[token_id].revoked = True
        return True

    async def delete(self, token_id: str) -> bool:
        """Delete a token"""
        if token_id not in self.tokens:
            return False

        token = self.tokens[token_id]

        # Remove from indexes
        del self.token_index[token.token]
        if token.user_id in self.user_tokens:
            self.user_tokens[token.user_id].remove(token_id)

        del self.tokens[token_id]
        return True

    async def delete_expired(self) -> int:
        """Delete all expired tokens"""
        now = datetime.utcnow()
        expired_ids = [
            token_id for token_id, token in self.tokens.items()
            if token.expires_at <= now
        ]

        count = 0
        for token_id in expired_ids:
            if await self.delete(token_id):
                count += 1

        return count