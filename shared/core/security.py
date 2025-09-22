"""Security middleware and authentication utilities."""

from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from .config import BaseConfig

# Security schemes
http_bearer = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class User(BaseModel):
    """User model for authentication."""

    id: str
    email: str
    role: str = "user"
    is_active: bool = True
    metadata: Dict[str, Any] = {}


class TokenData(BaseModel):
    """JWT token data."""

    sub: str  # User ID
    email: Optional[str] = None
    role: str = "user"
    exp: Optional[int] = None


async def decode_token(token: str, config: BaseConfig) -> TokenData:
    """Decode and validate JWT token.

    Args:
        token: JWT token string
        config: Application configuration

    Returns:
        TokenData from the decoded token

    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(
            token, config.secret_key, algorithms=[config.jwt_algorithm]
        )
        token_data = TokenData(**payload)
        return token_data
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(http_bearer),
) -> Optional[User]:
    """Get current user if authenticated, None otherwise.

    Args:
        credentials: Optional bearer token

    Returns:
        User if authenticated, None otherwise
    """
    if not credentials:
        return None

    try:
        # Import here to avoid circular dependency
        from ..utils.container import get_config

        config = get_config()
        token_data = await decode_token(credentials.credentials, config)

        # TODO: Fetch user from database using token_data.sub
        # For now, return a mock user
        user = User(
            id=token_data.sub,
            email=token_data.email or f"user_{token_data.sub}@example.com",
            role=token_data.role,
        )
        return user
    except HTTPException:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(http_bearer),
) -> User:
    """Get current authenticated user.

    Args:
        credentials: Bearer token

    Returns:
        Current user

    Raises:
        HTTPException: If not authenticated
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await get_current_user_optional(credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user if active

    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user"
        )
    return current_user


# Security group dependencies
async def public_endpoint() -> None:
    """Public endpoint - no authentication required."""
    return None


async def authenticated_endpoint(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Authenticated endpoint - requires valid user session.

    Args:
        current_user: Current authenticated user

    Returns:
        Authenticated user

    Raises:
        HTTPException: If not authenticated
    """
    return current_user


async def admin_endpoint(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Admin endpoint - requires admin role.

    Args:
        current_user: Current authenticated user

    Returns:
        Admin user

    Raises:
        HTTPException: If not admin
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def internal_endpoint(
    api_key: Optional[str] = Security(api_key_header),
) -> bool:
    """Internal endpoint - requires valid API key for service-to-service communication.

    Args:
        api_key: API key from header

    Returns:
        True if authorized

    Raises:
        HTTPException: If invalid API key
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key required",
        )

    # Import here to avoid circular dependency
    from ..utils.container import get_config

    config = get_config()

    if not config.internal_api_key or api_key != config.internal_api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )

    return True


def create_access_token(
    user_id: str,
    email: str,
    role: str,
    config: BaseConfig,
    expires_delta: Optional[int] = None,
) -> str:
    """Create a JWT access token.

    Args:
        user_id: User ID
        email: User email
        role: User role
        config: Application configuration
        expires_delta: Token expiration time in seconds

    Returns:
        JWT token string
    """
    from datetime import datetime, timedelta

    if expires_delta:
        expire = datetime.utcnow() + timedelta(seconds=expires_delta)
    else:
        expire = datetime.utcnow() + timedelta(hours=config.jwt_expiration_hours)

    token_data = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": expire,
    }

    token = jwt.encode(token_data, config.secret_key, algorithm=config.jwt_algorithm)
    return token


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password

    Returns:
        True if password matches
    """
    try:
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(plain_password, hashed_password)
    except ImportError:
        # Fallback to simple comparison if passlib not installed
        # This should only be used in development
        import hashlib

        return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def get_password_hash(password: str) -> str:
    """Hash a password.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    try:
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)
    except ImportError:
        # Fallback to simple hashing if passlib not installed
        # This should only be used in development
        import hashlib

        return hashlib.sha256(password.encode()).hexdigest()
