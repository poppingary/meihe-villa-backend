"""Tests for visit info API endpoints."""

import pytest
from httpx import AsyncClient

from app.models.visit_info import VisitInfo


@pytest.fixture
async def visit_info(db_session):
    """Create a test visit info."""
    info = VisitInfo(
        section="transportation",
        title="Getting Here",
        title_zh="交通資訊",
        content="How to get to the villa",
        content_zh="如何前往山莊",
        extra_data='{"電話": "03-332-2592", "phone_en": "03-332-2592"}',
        display_order=1,
        is_active=True,
    )
    db_session.add(info)
    await db_session.flush()
    await db_session.refresh(info)
    return info


@pytest.fixture
async def inactive_visit_info(db_session):
    """Create an inactive visit info."""
    info = VisitInfo(
        section="old-section",
        title="Old Section",
        title_zh="舊區塊",
        is_active=False,
    )
    db_session.add(info)
    await db_session.flush()
    await db_session.refresh(info)
    return info


class TestListVisitInfo:
    """Tests for list visit info endpoint."""

    @pytest.mark.asyncio
    async def test_list_visit_info_empty(self, client: AsyncClient):
        """Test listing visit info when empty."""
        response = await client.get("/api/v1/visit-info")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_visit_info_with_items(self, client: AsyncClient, visit_info):
        """Test listing visit info with items."""
        response = await client.get("/api/v1/visit-info")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["section"] == "transportation"
        assert data[0]["title"] == "Getting Here"

    @pytest.mark.asyncio
    async def test_list_visit_info_excludes_inactive(
        self, client: AsyncClient, visit_info, inactive_visit_info
    ):
        """Test that inactive visit info is excluded by default."""
        response = await client.get("/api/v1/visit-info")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["section"] == "transportation"

    @pytest.mark.asyncio
    async def test_list_visit_info_include_inactive(
        self, client: AsyncClient, visit_info, inactive_visit_info
    ):
        """Test listing all visit info including inactive."""
        response = await client.get("/api/v1/visit-info?active_only=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_list_visit_info_ordered_by_display_order(
        self, client: AsyncClient, db_session
    ):
        """Test that visit info is ordered by display_order."""
        info1 = VisitInfo(
            section="section-3",
            title="Third",
            title_zh="第三",
            display_order=3,
            is_active=True,
        )
        info2 = VisitInfo(
            section="section-1",
            title="First",
            title_zh="第一",
            display_order=1,
            is_active=True,
        )
        db_session.add_all([info1, info2])
        await db_session.flush()

        response = await client.get("/api/v1/visit-info")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["display_order"] == 1
        assert data[1]["display_order"] == 3


class TestGetVisitInfo:
    """Tests for get visit info by ID endpoint."""

    @pytest.mark.asyncio
    async def test_get_visit_info_by_id(self, client: AsyncClient, visit_info):
        """Test getting visit info by ID."""
        response = await client.get(f"/api/v1/visit-info/{visit_info.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["section"] == "transportation"
        assert data["title"] == "Getting Here"

    @pytest.mark.asyncio
    async def test_get_visit_info_not_found(self, client: AsyncClient):
        """Test getting non-existent visit info."""
        response = await client.get("/api/v1/visit-info/9999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetVisitInfoBySection:
    """Tests for get visit info by section endpoint."""

    @pytest.mark.asyncio
    async def test_get_visit_info_by_section(self, client: AsyncClient, visit_info):
        """Test getting visit info by section."""
        response = await client.get("/api/v1/visit-info/section/transportation")
        assert response.status_code == 200
        data = response.json()
        assert data["section"] == "transportation"
        assert data["title"] == "Getting Here"

    @pytest.mark.asyncio
    async def test_get_visit_info_by_section_not_found(self, client: AsyncClient):
        """Test getting visit info by non-existent section."""
        response = await client.get("/api/v1/visit-info/section/nonexistent")
        assert response.status_code == 404


class TestCreateVisitInfo:
    """Tests for create visit info endpoint."""

    @pytest.mark.asyncio
    async def test_create_visit_info(self, client: AsyncClient):
        """Test creating a visit info."""
        info_data = {
            "section": "hours",
            "title": "Opening Hours",
            "title_zh": "開放時間",
            "content": "9 AM to 5 PM",
            "display_order": 2,
        }
        response = await client.post("/api/v1/visit-info", json=info_data)
        assert response.status_code == 201
        data = response.json()
        assert data["section"] == "hours"
        assert data["title"] == "Opening Hours"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_visit_info_minimal(self, client: AsyncClient):
        """Test creating visit info with minimal required fields."""
        info_data = {
            "section": "minimal",
            "title": "Minimal Section",
            "title_zh": "最小區塊",
        }
        response = await client.post("/api/v1/visit-info", json=info_data)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_visit_info_with_extra_data(self, client: AsyncClient):
        """Test creating visit info with extra_data."""
        info_data = {
            "section": "contact",
            "title": "Contact",
            "title_zh": "聯絡方式",
            "extra_data": '{"電話": "123-456", "email": "test@example.com"}',
        }
        response = await client.post("/api/v1/visit-info", json=info_data)
        assert response.status_code == 201
        data = response.json()
        assert data["extra_data"] == '{"電話": "123-456", "email": "test@example.com"}'


class TestUpdateVisitInfo:
    """Tests for update visit info endpoint."""

    @pytest.mark.asyncio
    async def test_update_visit_info(self, client: AsyncClient, visit_info):
        """Test updating a visit info."""
        update_data = {"title": "Updated Title"}
        response = await client.patch(
            f"/api/v1/visit-info/{visit_info.id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        # Original fields should be preserved
        assert data["section"] == "transportation"

    @pytest.mark.asyncio
    async def test_update_visit_info_not_found(self, client: AsyncClient):
        """Test updating non-existent visit info."""
        update_data = {"title": "Updated Title"}
        response = await client.patch("/api/v1/visit-info/9999", json=update_data)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_visit_info_multiple_fields(
        self, client: AsyncClient, visit_info
    ):
        """Test updating multiple fields."""
        update_data = {
            "title": "New Title",
            "content": "New content",
            "display_order": 5,
            "is_active": False,
        }
        response = await client.patch(
            f"/api/v1/visit-info/{visit_info.id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["content"] == "New content"
        assert data["display_order"] == 5
        assert data["is_active"] is False


class TestDeleteVisitInfo:
    """Tests for delete visit info endpoint."""

    @pytest.mark.asyncio
    async def test_delete_visit_info(self, client: AsyncClient, visit_info):
        """Test deleting a visit info."""
        info_id = visit_info.id
        response = await client.delete(f"/api/v1/visit-info/{info_id}")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_visit_info_not_found(self, client: AsyncClient):
        """Test deleting non-existent visit info."""
        response = await client.delete("/api/v1/visit-info/9999")
        assert response.status_code == 404
