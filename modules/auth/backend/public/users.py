from modules.auth.backend.service.users import get_user
from modules.auth.backend.schemas.user import UserPublic


def get_user_public(user_id: int) -> UserPublic | None:
    """Public facade: safe, stable query.

    Example:
        >>> u = get_user_public(1)
        >>> u is None or u.id == 1
        True
    """
    u = get_user(user_id)
    return None if not u else UserPublic.model_validate(u.model_dump())

