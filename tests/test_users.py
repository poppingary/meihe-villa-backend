"""Tests for user management API endpoints."""

import uuid

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash
from app.models.user import User, UserRole


@pytest.fixture
async def superadmin(db_session):
    """Create a superadmin user."""
    user_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
    user = User(
        id=user_id,
        email="superadmin@test.com",
        password_hash=get_password_hash("superpass"),
        name="Super Admin",
        is_active=True,
        role=UserRole.SUPERADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def other_user(db_session):
    """Create another user for testing."""
    user_id = uuid.UUID("22222222-2222-2222-2222-222222222222")
    user = User(
        id=user_id,
        email="other@test.com",
        password_hash=get_password_hash("otherpass"),
        name="Other User",
        is_active=True,
        role=UserRole.ADMIN,
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest.fixture
def superadmin_token(superadmin):
    """Create auth token for superadmin."""
    return create_access_token({"sub": str(superadmin.id), "email": superadmin.email})


class TestListUsers:
    """Tests for list users endpoint."""

    @pytest.mark.asyncio
    async def test_list_users_as_superadmin(
        self, client: AsyncClient, superadmin, superadmin_token, other_user
    ):
        """Test listing users as superadmin."""
        client.cookies.set("access_token", superadmin_token)
        response = await client.get("/api/v1/users")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_list_users_unauthorized(self, client: AsyncClient):
        """Test listing users without authentication."""
        response = await client.get("/api/v1/users")
        assert response.status_code == 401


class TestGetUser:
    """Tests for get user endpoint."""

    @pytest.mark.asyncio
    async def test_get_user_by_id(
        self, client: AsyncClient, superadmin, superadmin_token, other_user
    ):
        """Test getting a user by ID."""
        client.cookies.set("access_token", superadmin_token)
        response = await client.get(f"/api/v1/users/{other_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "other@test.com"

    @pytest.mark.asyncio
    async def test_get_user_not_found(
        self, client: AsyncClient, superadmin_token
    ):
        """Test getting non-existent user."""
        client.cookies.set("access_token", superadmin_token)
        fake_id = uuid.uuid4()
        response = await client.get(f"/api/v1/users/{fake_id}")
        assert response.status_code == 404


class TestCreateUser:
    """Tests for create user endpoint."""

    @pytest.mark.asyncio
    async def test_create_user(self, client: AsyncClient, superadmin_token):
        """Test creating a new user."""
        client.cookies.set("access_token", superadmin_token)
        user_data = {
            "email": "newuser@test.com",
            "password": "newpassword",
            "name": "New User",
            "role": "admin",
        }
        response = await client.post("/api/v1/users", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["name"] == "New User"

    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(
        self, client: AsyncClient, superadmin, superadmin_token
    ):
        """Test creating user with duplicate email."""
        client.cookies.set("access_token", superadmin_token)
        user_data = {
            "email": "superadmin@test.com",  # Same as superadmin
            "password": "somepassword",
            "name": "Duplicate",
        }
        response = await client.post("/api/v1/users", json=user_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]


class TestUpdateUser:
    """Tests for update user endpoint."""

    @pytest.mark.asyncio
    async def test_update_user(
        self, client: AsyncClient, superadmin, superadmin_token, other_user
    ):
        """Test updating a user."""
        client.cookies.set("access_token", superadmin_token)
        update_data = {"name": "Updated Name"}
        response = await client.patch(
            f"/api/v1/users/{other_user.id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    @pytest.mark.asyncio
    async def test_update_user_not_found(self, client: AsyncClient, superadmin_token):
        """Test updating non-existent user."""
        client.cookies.set("access_token", superadmin_token)
        fake_id = uuid.uuid4()
        response = await client.patch(f"/api/v1/users/{fake_id}", json={"name": "X"})
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cannot_change_own_role(
        self, client: AsyncClient, superadmin, superadmin_token
    ):
        """Test that superadmin cannot change their own role."""
        client.cookies.set("access_token", superadmin_token)
        update_data = {"role": "admin"}
        response = await client.patch(
            f"/api/v1/users/{superadmin.id}", json=update_data
        )
        assert response.status_code == 400
        assert "own role" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_cannot_deactivate_self(
        self, client: AsyncClient, superadmin, superadmin_token
    ):
        """Test that superadmin cannot deactivate themselves."""
        client.cookies.set("access_token", superadmin_token)
        update_data = {"is_active": False}
        response = await client.patch(
            f"/api/v1/users/{superadmin.id}", json=update_data
        )
        assert response.status_code == 400
        assert "own account" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_user_duplicate_email(
        self, client: AsyncClient, superadmin, superadmin_token, other_user
    ):
        """Test updating user with duplicate email."""
        client.cookies.set("access_token", superadmin_token)
        update_data = {"email": "superadmin@test.com"}  # Same as superadmin
        response = await client.patch(
            f"/api/v1/users/{other_user.id}", json=update_data
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_user_password(
        self, client: AsyncClient, superadmin_token, other_user
    ):
        """Test updating user password."""
        client.cookies.set("access_token", superadmin_token)
        update_data = {"password": "newpassword123"}
        response = await client.patch(
            f"/api/v1/users/{other_user.id}", json=update_data
        )
        assert response.status_code == 200


class TestDeleteUser:
    """Tests for delete user endpoint."""

    @pytest.mark.asyncio
    async def test_delete_user(
        self, client: AsyncClient, superadmin_token, other_user
    ):
        """Test deleting a user."""
        client.cookies.set("access_token", superadmin_token)
        response = await client.delete(f"/api/v1/users/{other_user.id}")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self, client: AsyncClient, superadmin_token):
        """Test deleting non-existent user."""
        client.cookies.set("access_token", superadmin_token)
        fake_id = uuid.uuid4()
        response = await client.delete(f"/api/v1/users/{fake_id}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cannot_delete_self(
        self, client: AsyncClient, superadmin, superadmin_token
    ):
        """Test that superadmin cannot delete themselves."""
        client.cookies.set("access_token", superadmin_token)
        response = await client.delete(f"/api/v1/users/{superadmin.id}")
        assert response.status_code == 400
        assert "own account" in response.json()["detail"].lower()
