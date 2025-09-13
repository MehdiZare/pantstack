from pydantic import BaseModel, EmailStr


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
