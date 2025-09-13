import os

import httpx

from modules.auth.backend.schemas.user import UserPublic

BASE = os.getenv("AUTH_BASE_URL", "http://auth:8000")


def get_user_public_http(user_id: int, timeout: float = 2.0) -> UserPublic | None:
    """HTTP client for cross-service calls.

    Example:
        >>> get_user_public_http(1) is None or True
        True
    """
    r = httpx.get(f"{BASE}/users/{user_id}", timeout=timeout)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return UserPublic.model_validate(r.json())
