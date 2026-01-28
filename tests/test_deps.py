"""Tests for API dependencies."""

import uuid

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash
from app.models.user import User, UserRole


@pytest.fixture
async def admin_user(db_session):
    """Create an admin user."""
    user_id = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
    user = User(
        id=user_id,
        email="admin@example.com",
        password_hash=get_password_hash("adminpassword"),
        name="Admin User",
        is_active=True,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def superadmin_user(db_session):
    """Create a superadmin user."""
    user_id = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")
    user = User(
        id=user_id,
        email="superadmin@example.com",
        password_hash=get_password_hash("superadminpassword"),
        name="Super Admin",
        is_active=True,
        role=UserRole.SUPERADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def inactive_admin(db_session):
    """Create an inactive admin user."""
    user_id = uuid.UUID("cccccccc-cccc-cccc-cccc-cccccccccccc")
    user = User(
        id=user_id,
        email="inactive_admin@example.com",
        password_hash=get_password_hash("password"),
        name="Inactive Admin",
        is_active=False,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


class TestCookieAuthentication:
    """Tests for cookie-based authentication."""

    @pytest.mark.asyncio
    async def test_auth_with_valid_cookie(self, client: AsyncClient, admin_user):
        """Test authentication with valid cookie."""
        token = create_access_token(
            {"sub": str(admin_user.id), "email": admin_user.email}
        )
        client.cookies.set("access_token", token)
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@example.com"

    @pytest.mark.asyncio
    async def test_auth_without_cookie(self, client: AsyncClient):
        """Test authentication without cookie."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_auth_with_invalid_cookie(self, client: AsyncClient):
        """Test authentication with invalid cookie token."""
        client.cookies.set("access_token", "invalid-token-here")
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_auth_with_inactive_user(self, client: AsyncClient, inactive_admin):
        """Test authentication with inactive user cookie."""
        token = create_access_token(
            {"sub": str(inactive_admin.id), "email": inactive_admin.email}
        )
        client.cookies.set("access_token", token)
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_auth_with_nonexistent_user_id(self, client: AsyncClient):
        """Test authentication with token containing non-existent user ID."""
        import uuid

        fake_id = str(uuid.uuid4())
        token = create_access_token({"sub": fake_id, "email": "fake@example.com"})
        client.cookies.set("access_token", token)
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 404


class TestSuperadminAccess:
    """Tests for superadmin-only access."""

    @pytest.mark.asyncio
    async def test_superadmin_can_access(self, client: AsyncClient, superadmin_user):
        """Test that superadmin can access protected resources."""
        token = create_access_token(
            {"sub": str(superadmin_user.id), "email": superadmin_user.email}
        )
        client.cookies.set("access_token", token)
        # Try to access users list (superadmin only)
        response = await client.get("/api/v1/users")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_cannot_access_superadmin_resources(
        self, client: AsyncClient, admin_user
    ):
        """Test that regular admin cannot access superadmin resources."""
        token = create_access_token(
            {"sub": str(admin_user.id), "email": admin_user.email}
        )
        client.cookies.set("access_token", token)
        # Try to access users list (superadmin only)
        response = await client.get("/api/v1/users")
        assert response.status_code == 403
        assert "Superadmin" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_unauthenticated_cannot_access_superadmin_resources(
        self, client: AsyncClient
    ):
        """Test that unauthenticated user cannot access superadmin resources."""
        response = await client.get("/api/v1/users")
        assert response.status_code == 401


class TestUserRole:
    """Tests for user role functionality."""

    @pytest.mark.asyncio
    async def test_user_is_superadmin_property(self, superadmin_user):
        """Test is_superadmin property returns True for superadmin."""
        assert superadmin_user.is_superadmin is True

    @pytest.mark.asyncio
    async def test_user_is_not_superadmin_property(self, admin_user):
        """Test is_superadmin property returns False for regular admin."""
        assert admin_user.is_superadmin is False
