"""Pydantic schemas for user module."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = Field(default="user")
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)


class UserCreate(UserBase):
    """User creation schema."""

    password_hash: str


class UserUpdate(BaseModel):
    """User update schema."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class User(UserBase):
    """User schema with all fields."""

    id: str
    password_hash: str
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        """Pydantic config."""

        from_attributes = True


class UserProfile(BaseModel):
    """User profile schema (public)."""

    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None


class UserList(BaseModel):
    """User list response."""

    users: list[UserProfile]
    total: int
    page: int = 1
    page_size: int = 20