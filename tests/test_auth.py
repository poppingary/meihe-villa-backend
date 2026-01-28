"""Tests for authentication endpoints."""

import uuid

import pytest
from httpx import AsyncClient

from app.core.security import get_password_hash, create_access_token
from app.models.user import User, UserRole


@pytest.fixture
async def test_user(db_session):
    """Create a test user for authentication tests."""
    # Use a fixed UUID for testing consistency
    user_id = uuid.UUID("12345678-1234-5678-1234-567812345678")
    user = User(
        id=user_id,
        email="test@example.com",
        password_hash=get_password_hash("testpassword123"),
        name="Test User",
        is_active=True,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def inactive_user(db_session):
    """Create an inactive test user."""
    user_id = uuid.UUID("87654321-4321-8765-4321-876543218765")
    user = User(
        id=user_id,
        email="inactive@example.com",
        password_hash=get_password_hash("testpassword123"),
        name="Inactive User",
        is_active=False,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_token(test_user):
    """Create an auth token for the test user."""
    return create_access_token({"sub": str(test_user.id), "email": test_user.email})


class TestLogin:
    """Tests for login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user):
        """Test successful login."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "testpassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert data["user"]["email"] == "test@example.com"
        assert "message" in data
        assert "access_token" in response.cookies

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Test login with wrong password."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "anypassword"},
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_inactive_user(self, client: AsyncClient, inactive_user):
        """Test login with inactive user."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": "testpassword123"},
        )
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"].lower()


class TestLogout:
    """Tests for logout endpoint."""

    @pytest.mark.asyncio
    async def test_logout(self, client: AsyncClient):
        """Test logout endpoint."""
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestGetCurrentUser:
    """Tests for get current user endpoint."""

    @pytest.mark.asyncio
    async def test_get_me_authenticated(self, client: AsyncClient, test_user, auth_token):
        """Test getting current user when authenticated."""
        client.cookies.set("access_token", auth_token)
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"

    @pytest.mark.asyncio
    async def test_get_me_not_authenticated(self, client: AsyncClient):
        """Test getting current user when not authenticated."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        client.cookies.set("access_token", "invalid-token")
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_me_inactive_user(self, client: AsyncClient, inactive_user):
        """Test getting current user when user is inactive."""
        token = create_access_token(
            {"sub": str(inactive_user.id), "email": inactive_user.email}
        )
        client.cookies.set("access_token", token)
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_me_malformed_uuid_in_token(self, client: AsyncClient):
        """Test getting current user with malformed UUID in token."""
        # Create a token with an invalid UUID
        token = create_access_token({"sub": "not-a-valid-uuid", "email": "test@test.com"})
        client.cookies.set("access_token", token)
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
        assert "Invalid token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_me_missing_sub_in_token(self, client: AsyncClient):
        """Test getting current user with token missing sub claim."""
        token = create_access_token({"email": "test@test.com"})  # Missing 'sub'
        client.cookies.set("access_token", token)
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
