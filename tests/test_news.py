"""Tests for news API endpoints."""

import pytest
from datetime import datetime, timezone
from httpx import AsyncClient

from app.models.news import News


@pytest.fixture
async def news_item(db_session):
    """Create a test news item."""
    news = News(
        title="Test News",
        title_zh="測試新聞",
        slug="test-news",
        summary="Test summary",
        summary_zh="測試摘要",
        content="Test content",
        content_zh="測試內容",
        category="announcement",
        is_published=True,
        published_at=datetime.now(timezone.utc),
    )
    db_session.add(news)
    await db_session.flush()
    await db_session.refresh(news)
    return news


@pytest.fixture
async def unpublished_news(db_session):
    """Create an unpublished news item."""
    news = News(
        title="Unpublished News",
        title_zh="未發布新聞",
        slug="unpublished-news",
        is_published=False,
    )
    db_session.add(news)
    await db_session.flush()
    await db_session.refresh(news)
    return news


class TestListNews:
    """Tests for list news endpoint."""

    @pytest.mark.asyncio
    async def test_list_news_empty(self, client: AsyncClient):
        """Test listing news when empty."""
        response = await client.get("/api/v1/news")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_news_with_items(self, client: AsyncClient, news_item):
        """Test listing news with items."""
        response = await client.get("/api/v1/news")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test News"
        assert data[0]["slug"] == "test-news"

    @pytest.mark.asyncio
    async def test_list_news_excludes_unpublished(
        self, client: AsyncClient, news_item, unpublished_news
    ):
        """Test that unpublished news is excluded by default."""
        response = await client.get("/api/v1/news")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Test News"

    @pytest.mark.asyncio
    async def test_list_news_include_unpublished(
        self, client: AsyncClient, news_item, unpublished_news
    ):
        """Test listing all news including unpublished."""
        response = await client.get("/api/v1/news?published_only=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_list_news_filter_by_category(self, client: AsyncClient, db_session):
        """Test filtering news by category."""
        news1 = News(
            title="News 1",
            title_zh="新聞1",
            slug="news-1",
            category="announcement",
            is_published=True,
        )
        news2 = News(
            title="News 2",
            title_zh="新聞2",
            slug="news-2",
            category="event",
            is_published=True,
        )
        db_session.add_all([news1, news2])
        await db_session.flush()

        response = await client.get("/api/v1/news?category=announcement")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "announcement"

    @pytest.mark.asyncio
    async def test_list_news_pagination(self, client: AsyncClient, db_session):
        """Test news pagination."""
        for i in range(5):
            news = News(
                title=f"News {i}",
                title_zh=f"新聞{i}",
                slug=f"news-{i}",
                is_published=True,
            )
            db_session.add(news)
        await db_session.flush()

        response = await client.get("/api/v1/news?limit=2")
        assert response.status_code == 200
        assert len(response.json()) == 2


class TestGetNews:
    """Tests for get news by ID endpoint."""

    @pytest.mark.asyncio
    async def test_get_news_by_id(self, client: AsyncClient, news_item):
        """Test getting news by ID."""
        response = await client.get(f"/api/v1/news/{news_item.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test News"
        assert data["id"] == news_item.id

    @pytest.mark.asyncio
    async def test_get_news_not_found(self, client: AsyncClient):
        """Test getting non-existent news."""
        response = await client.get("/api/v1/news/9999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetNewsBySlug:
    """Tests for get news by slug endpoint."""

    @pytest.mark.asyncio
    async def test_get_news_by_slug(self, client: AsyncClient, news_item):
        """Test getting news by slug."""
        response = await client.get("/api/v1/news/slug/test-news")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test News"
        assert data["slug"] == "test-news"

    @pytest.mark.asyncio
    async def test_get_news_by_slug_not_found(self, client: AsyncClient):
        """Test getting news by non-existent slug."""
        response = await client.get("/api/v1/news/slug/nonexistent-slug")
        assert response.status_code == 404


class TestCreateNews:
    """Tests for create news endpoint."""

    @pytest.mark.asyncio
    async def test_create_news(self, client: AsyncClient):
        """Test creating a news item."""
        news_data = {
            "title": "New Article",
            "title_zh": "新文章",
            "slug": "new-article",
            "summary": "A new article summary",
            "is_published": True,
        }
        response = await client.post("/api/v1/news", json=news_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Article"
        assert data["slug"] == "new-article"
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_news_minimal(self, client: AsyncClient):
        """Test creating news with minimal required fields."""
        news_data = {
            "title": "Minimal News",
            "title_zh": "最小新聞",
            "slug": "minimal-news",
        }
        response = await client.post("/api/v1/news", json=news_data)
        assert response.status_code == 201


class TestUpdateNews:
    """Tests for update news endpoint."""

    @pytest.mark.asyncio
    async def test_update_news(self, client: AsyncClient, news_item):
        """Test updating a news item."""
        update_data = {"title": "Updated Title"}
        response = await client.patch(
            f"/api/v1/news/{news_item.id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        # Original fields should be preserved
        assert data["title_zh"] == "測試新聞"

    @pytest.mark.asyncio
    async def test_update_news_not_found(self, client: AsyncClient):
        """Test updating non-existent news."""
        update_data = {"title": "Updated Title"}
        response = await client.patch("/api/v1/news/9999", json=update_data)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_news_multiple_fields(self, client: AsyncClient, news_item):
        """Test updating multiple fields."""
        update_data = {
            "title": "New Title",
            "summary": "New summary",
            "is_published": False,
        }
        response = await client.patch(
            f"/api/v1/news/{news_item.id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["summary"] == "New summary"
        assert data["is_published"] is False


class TestDeleteNews:
    """Tests for delete news endpoint."""

    @pytest.mark.asyncio
    async def test_delete_news(self, client: AsyncClient, news_item):
        """Test deleting a news item."""
        news_id = news_item.id
        response = await client.delete(f"/api/v1/news/{news_id}")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_news_not_found(self, client: AsyncClient):
        """Test deleting non-existent news."""
        response = await client.delete("/api/v1/news/9999")
        assert response.status_code == 404
