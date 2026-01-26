"""Authentication schemas."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr


class UserRole(str, Enum):
    """User role enum."""

    ADMIN = "admin"
    SUPERADMIN = "superadmin"


class LoginRequest(BaseModel):
    """Login request schema."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response schema."""

    id: uuid.UUID
    email: str
    name: str | None
    is_active: bool
    role: UserRole
    created_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """User create schema."""

    email: EmailStr
    password: str
    name: str | None = None
    role: UserRole = UserRole.ADMIN


class UserUpdate(BaseModel):
    """User update schema."""

    email: EmailStr | None = None
    password: str | None = None
    name: str | None = None
    is_active: bool | None = None
    role: UserRole | None = None


class UserListResponse(BaseModel):
    """User list response schema."""

    items: list[UserResponse]
    total: int


class LoginResponse(BaseModel):
    """Login response schema."""

    user: UserResponse
    message: str = "Login successful"


class LogoutResponse(BaseModel):
    """Logout response schema."""

    message: str = "Logged out successfully"
