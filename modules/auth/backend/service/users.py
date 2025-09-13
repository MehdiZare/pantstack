from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int
    email: EmailStr
    is_active: bool = True


_FAKE_DB = {
    1: User(id=1, email="user1@example.com", is_active=True),
    2: User(id=2, email="user2@example.com", is_active=False),
}


def get_user(user_id: int) -> User | None:
    """Return a domain user or None.

    Example:
        >>> u = get_user(1)
        >>> u and u.id == 1
        True
    """
    return _FAKE_DB.get(user_id)

