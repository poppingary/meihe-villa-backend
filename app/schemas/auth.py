"""Authentication schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


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
    created_at: datetime

    model_config = {"from_attributes": True}


class LoginResponse(BaseModel):
    """Login response schema."""

    user: UserResponse
    message: str = "Login successful"


class LogoutResponse(BaseModel):
    """Logout response schema."""

    message: str = "Logged out successfully"
