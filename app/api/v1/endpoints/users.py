"""User management endpoints (superadmin only)."""

import uuid

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import DbSession, SuperAdminUser
from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.auth import UserCreate, UserListResponse, UserResponse, UserUpdate

router = APIRouter()


@router.get("", response_model=UserListResponse)
async def list_users(
    db: DbSession,
    _: SuperAdminUser,
):
    """List all users (superadmin only)."""
    # Get total count
    count_query = select(func.count()).select_from(User)
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Get all users
    query = select(User).order_by(User.created_at.desc())
    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        items=[UserResponse.model_validate(user) for user in users],
        total=total,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    db: DbSession,
    _: SuperAdminUser,
    user_id: uuid.UUID,
):
    """Get a single user by ID (superadmin only)."""
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    db: DbSession,
    _: SuperAdminUser,
    user_in: UserCreate,
):
    """Create a new user (superadmin only)."""
    # Check if email already exists
    existing_query = select(User).where(User.email == user_in.email)
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Create user
    user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
        name=user_in.name,
        role=user_in.role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    db: DbSession,
    current_user: SuperAdminUser,
    user_id: uuid.UUID,
    user_in: UserUpdate,
):
    """Update a user (superadmin only)."""
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent superadmin from demoting themselves
    if user.id == current_user.id and user_in.role and user_in.role != user.role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role",
        )

    # Prevent superadmin from deactivating themselves
    if user.id == current_user.id and user_in.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )

    # Check email uniqueness if changing
    if user_in.email and user_in.email != user.email:
        existing_query = select(User).where(User.email == user_in.email)
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )

    # Update fields
    update_data = user_in.model_dump(exclude_unset=True)

    # Handle password separately
    if "password" in update_data:
        password = update_data.pop("password")
        if password:
            user.password_hash = get_password_hash(password)

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    db: DbSession,
    current_user: SuperAdminUser,
    user_id: uuid.UUID,
):
    """Delete a user (superadmin only)."""
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent superadmin from deleting themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    await db.delete(user)
