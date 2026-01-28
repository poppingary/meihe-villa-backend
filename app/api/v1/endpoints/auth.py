"""Authentication endpoints."""

import uuid
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import select

from app.api.deps import DbSession
from app.config import get_settings
from app.core.security import (
    create_access_token,
    verify_password,
    verify_token,
)
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, LogoutResponse, UserResponse

router = APIRouter()
settings = get_settings()

COOKIE_NAME = "access_token"


def set_auth_cookie(response: Response, token: str) -> None:
    """Set the authentication cookie."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        max_age=settings.access_token_expire_hours * 3600,
        path="/",
        domain=settings.cookie_domain or None,
    )


def clear_auth_cookie(response: Response) -> None:
    """Clear the authentication cookie."""
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        domain=settings.cookie_domain or None,
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    db: DbSession,
    login_data: LoginRequest,
    response: Response,
):
    """Authenticate user and set cookie."""
    # Find user by email
    query = select(User).where(User.email == login_data.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    # Create token
    token = create_access_token(
        data={"sub": str(user.id), "email": user.email},
        expires_delta=timedelta(hours=settings.access_token_expire_hours),
    )

    # Set cookie
    set_auth_cookie(response, token)

    return LoginResponse(user=UserResponse.model_validate(user))


@router.post("/logout", response_model=LogoutResponse)
async def logout(response: Response):
    """Clear authentication cookie."""
    clear_auth_cookie(response)
    return LogoutResponse()


@router.get("/me", response_model=UserResponse)
async def get_current_user(db: DbSession, request: Request):
    """Get current authenticated user."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )

    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        user_id = uuid.UUID(user_id_str)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )

    return user
