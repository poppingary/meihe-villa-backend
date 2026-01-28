"""Tests for heritage API endpoints."""

import pytest
from httpx import AsyncClient

from app.models.heritage import HeritageCategory, HeritageSite


@pytest.fixture
async def category(db_session):
    """Create a test category."""
    cat = HeritageCategory(
        name="Historic Houses",
        name_zh="歷史建築",
        description="Historic residential buildings",
    )
    db_session.add(cat)
    await db_session.flush()
    await db_session.refresh(cat)
    return cat


@pytest.fixture
async def heritage_site(db_session, category):
    """Create a test heritage site."""
    from datetime import datetime, timezone

    site = HeritageSite(
        name="Meihe Villa",
        name_zh="梅鶴山莊",
        slug="meihe-villa",
        city="Taoyuan",
        description="A historic villa",
        description_zh="歷史山莊",
        category_id=category.id,
        is_published=True,
        # Set timestamps explicitly for SQLite compatibility
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db_session.add(site)
    await db_session.flush()
    await db_session.refresh(site)
    return site


@pytest.fixture
async def unpublished_site(db_session):
    """Create an unpublished heritage site."""
    site = HeritageSite(
        name="Unpublished Site",
        name_zh="未發布景點",
        slug="unpublished-site",
        city="Taipei",
        is_published=False,
    )
    db_session.add(site)
    await db_session.flush()
    await db_session.refresh(site)
    return site


class TestListHeritageSites:
    """Tests for list heritage sites endpoint."""

    @pytest.mark.asyncio
    async def test_list_sites_empty(self, client: AsyncClient):
        """Test listing sites when empty."""
        response = await client.get("/api/v1/heritage/sites")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_sites_with_items(
        self, client: AsyncClient, heritage_site, category
    ):
        """Test listing sites with items."""
        response = await client.get("/api/v1/heritage/sites")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Meihe Villa"
        assert data[0]["slug"] == "meihe-villa"

    @pytest.mark.asyncio
    async def test_list_sites_excludes_unpublished(
        self, client: AsyncClient, heritage_site, unpublished_site
    ):
        """Test that unpublished sites are excluded by default."""
        response = await client.get("/api/v1/heritage/sites")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Meihe Villa"

    @pytest.mark.asyncio
    async def test_list_sites_include_unpublished(
        self, client: AsyncClient, heritage_site, unpublished_site
    ):
        """Test listing all sites including unpublished."""
        response = await client.get("/api/v1/heritage/sites?published_only=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_list_sites_filter_by_city(
        self, client: AsyncClient, db_session, category
    ):
        """Test filtering sites by city."""
        site1 = HeritageSite(
            name="Site 1",
            name_zh="景點1",
            slug="site-1",
            city="Taipei",
            is_published=True,
        )
        site2 = HeritageSite(
            name="Site 2",
            name_zh="景點2",
            slug="site-2",
            city="Taoyuan",
            is_published=True,
        )
        db_session.add_all([site1, site2])
        await db_session.flush()

        response = await client.get("/api/v1/heritage/sites?city=Taipei")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["city"] == "Taipei"

    @pytest.mark.asyncio
    async def test_list_sites_filter_by_category(
        self, client: AsyncClient, heritage_site, category
    ):
        """Test filtering sites by category_id."""
        response = await client.get(
            f"/api/v1/heritage/sites?category_id={category.id}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category_id"] == category.id

    @pytest.mark.asyncio
    async def test_list_sites_pagination(self, client: AsyncClient, db_session):
        """Test sites pagination."""
        for i in range(5):
            site = HeritageSite(
                name=f"Site {i}",
                name_zh=f"景點{i}",
                slug=f"site-{i}",
                city="Taipei",
                is_published=True,
            )
            db_session.add(site)
        await db_session.flush()

        response = await client.get("/api/v1/heritage/sites?limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2


class TestGetHeritageSite:
    """Tests for get heritage site by ID endpoint."""

    @pytest.mark.asyncio
    async def test_get_site_by_id(self, client: AsyncClient, heritage_site):
        """Test getting site by ID."""
        response = await client.get(f"/api/v1/heritage/sites/{heritage_site.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Meihe Villa"
        assert data["id"] == heritage_site.id

    @pytest.mark.asyncio
    async def test_get_site_not_found(self, client: AsyncClient):
        """Test getting non-existent site."""
        response = await client.get("/api/v1/heritage/sites/9999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetHeritageSiteBySlug:
    """Tests for get heritage site by slug endpoint."""

    @pytest.mark.asyncio
    async def test_get_site_by_slug(self, client: AsyncClient, heritage_site):
        """Test getting site by slug."""
        response = await client.get("/api/v1/heritage/sites/slug/meihe-villa")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Meihe Villa"
        assert data["slug"] == "meihe-villa"

    @pytest.mark.asyncio
    async def test_get_site_by_slug_not_found(self, client: AsyncClient):
        """Test getting site by non-existent slug."""
        response = await client.get("/api/v1/heritage/sites/slug/nonexistent")
        assert response.status_code == 404


class TestCreateHeritageSite:
    """Tests for create heritage site endpoint."""

    @pytest.mark.asyncio
    async def test_create_site(self, client: AsyncClient, category):
        """Test creating a heritage site."""
        site_data = {
            "name": "New Villa",
            "name_zh": "新山莊",
            "slug": "new-villa",
            "city": "Taipei",
            "description": "A new heritage site",
            "category_id": category.id,
            "is_published": True,
        }
        response = await client.post("/api/v1/heritage/sites", json=site_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "New Villa"
        assert data["slug"] == "new-villa"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_site_minimal(self, client: AsyncClient):
        """Test creating site with minimal required fields."""
        site_data = {
            "name": "Minimal Site",
            "name_zh": "最小景點",
            "slug": "minimal-site",
            "city": "Taipei",
        }
        response = await client.post("/api/v1/heritage/sites", json=site_data)
        assert response.status_code == 201


class TestUpdateHeritageSite:
    """Tests for update heritage site endpoint."""

    @pytest.mark.asyncio
    async def test_update_site(self, client: AsyncClient, heritage_site):
        """Test updating a heritage site."""
        update_data = {"name": "Updated Villa"}
        response = await client.patch(
            f"/api/v1/heritage/sites/{heritage_site.id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Villa"
        # Original fields should be preserved
        assert data["slug"] == "meihe-villa"

    @pytest.mark.asyncio
    async def test_update_site_not_found(self, client: AsyncClient):
        """Test updating non-existent site."""
        update_data = {"name": "Updated Villa"}
        response = await client.patch("/api/v1/heritage/sites/9999", json=update_data)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_site_multiple_fields(
        self, client: AsyncClient, heritage_site
    ):
        """Test updating multiple fields."""
        update_data = {
            "name": "New Name",
            "description": "New description",
            "is_published": False,
        }
        response = await client.patch(
            f"/api/v1/heritage/sites/{heritage_site.id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["description"] == "New description"
        assert data["is_published"] is False


class TestDeleteHeritageSite:
    """Tests for delete heritage site endpoint."""

    @pytest.mark.asyncio
    async def test_delete_site(self, client: AsyncClient, heritage_site):
        """Test deleting a heritage site."""
        site_id = heritage_site.id
        response = await client.delete(f"/api/v1/heritage/sites/{site_id}")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_site_not_found(self, client: AsyncClient):
        """Test deleting non-existent site."""
        response = await client.delete("/api/v1/heritage/sites/9999")
        assert response.status_code == 404


class TestHeritageCategories:
    """Tests for heritage category endpoints."""

    @pytest.mark.asyncio
    async def test_list_categories_empty(self, client: AsyncClient):
        """Test listing categories when empty."""
        response = await client.get("/api/v1/heritage/categories")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_categories_with_items(self, client: AsyncClient, category):
        """Test listing categories with items."""
        response = await client.get("/api/v1/heritage/categories")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Historic Houses"

    @pytest.mark.asyncio
    async def test_create_category(self, client: AsyncClient):
        """Test creating a category."""
        category_data = {
            "name": "Temples",
            "name_zh": "寺廟",
            "description": "Buddhist and Taoist temples",
        }
        response = await client.post(
            "/api/v1/heritage/categories", json=category_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Temples"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_category_minimal(self, client: AsyncClient):
        """Test creating category with minimal fields."""
        category_data = {
            "name": "Minimal",
            "name_zh": "最小",
        }
        response = await client.post(
            "/api/v1/heritage/categories", json=category_data
        )
        assert response.status_code == 201
