"""Authentication domain service"""
from typing import Optional, Tuple
import hashlib
import secrets

from ..models import User, Token, TokenType
from ..ports import UserRepository, TokenRepository


class AuthenticationService:
    """Handles authentication business logic"""

    def __init__(self, user_repo: UserRepository, token_repo: TokenRepository):
        self.user_repo = user_repo
        self.token_repo = token_repo

    async def authenticate(self, email: str, password: str) -> Tuple[Optional[User], Optional[Token]]:
        """Authenticate a user with email and password"""
        user = await self.user_repo.find_by_email(email)

        if not user or not user.can_login():
            return None, None

        if not self._verify_password(password, user.hashed_password):
            return None, None

        # Generate access token
        token = await self._generate_token(user.id, TokenType.ACCESS)

        return user, token

    async def register(self, email: str, username: str, password: str) -> User:
        """Register a new user"""
        # Check if user exists
        existing_user = await self.user_repo.find_by_email(email)
        if existing_user:
            raise ValueError("User with this email already exists")

        # Hash password
        hashed_password = self._hash_password(password)

        # Create user
        user = await self.user_repo.create(
            email=email,
            username=username,
            hashed_password=hashed_password
        )

        # Generate verification token
        await self._generate_token(user.id, TokenType.VERIFICATION)

        return user

    async def verify_token(self, token_string: str) -> Optional[User]:
        """Verify a token and return the associated user"""
        token = await self.token_repo.find_by_token(token_string)

        if not token or not token.is_valid():
            return None

        user = await self.user_repo.find_by_id(token.user_id)
        return user

    async def refresh_token(self, refresh_token: str) -> Optional[Token]:
        """Refresh an access token using a refresh token"""
        token = await self.token_repo.find_by_token(refresh_token)

        if not token or token.token_type != TokenType.REFRESH or not token.is_valid():
            return None

        # Generate new access token
        new_token = await self._generate_token(token.user_id, TokenType.ACCESS)

        # Revoke old refresh token
        await self.token_repo.revoke(token.id)

        return new_token

    def _hash_password(self, password: str) -> str:
        """Hash a password"""
        salt = secrets.token_hex(32)
        pwdhash = hashlib.pbkdf2_hmac('sha256',
                                      password.encode('utf-8'),
                                      salt.encode('utf-8'),
                                      100000)
        return f"{salt}${pwdhash.hex()}"

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify a password against a hash"""
        try:
            salt, pwdhash = hashed.split('$')
            expected = hashlib.pbkdf2_hmac('sha256',
                                          password.encode('utf-8'),
                                          salt.encode('utf-8'),
                                          100000)
            return expected.hex() == pwdhash
        except (ValueError, AttributeError):
            return False

    async def _generate_token(self, user_id: str, token_type: TokenType) -> Token:
        """Generate a new token"""
        token_string = secrets.token_urlsafe(32)
        token = await self.token_repo.create(
            user_id=user_id,
            token_type=token_type,
            token=token_string
        )
        return token