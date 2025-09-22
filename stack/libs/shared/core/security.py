"""Security utilities for password hashing and JWT token management."""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import jwt
from passlib.context import CryptContext

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a plain text password.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    secret_key: str,
    expires_delta: Optional[timedelta] = None,
    algorithm: str = "HS256",
) -> str:
    """Create a JWT access token.

    Args:
        data: Data to encode in the token
        secret_key: Secret key for signing the token
        expires_delta: Token expiration time delta
        algorithm: JWT signing algorithm

    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt


def decode_access_token(
    token: str, secret_key: str, algorithm: str = "HS256"
) -> Dict[str, Any]:
    """Decode a JWT access token.

    Args:
        token: JWT token to decode
        secret_key: Secret key for verifying the token
        algorithm: JWT signing algorithm

    Returns:
        Decoded token data

    Raises:
        jwt.PyJWTError: If token is invalid or expired
    """
    return jwt.decode(token, secret_key, algorithms=[algorithm])
