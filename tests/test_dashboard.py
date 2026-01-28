"""Tests for dashboard API endpoints."""

import pytest
from httpx import AsyncClient

from app.models.heritage import HeritageCategory, HeritageSite
from app.models.news import News
from app.models.timeline import TimelineEvent
from app.models.visit_info import VisitInfo


class TestDashboardStats:
    """Tests for dashboard stats endpoint."""

    @pytest.mark.asyncio
    async def test_get_stats_empty(self, client: AsyncClient):
        """Test getting stats when database is empty."""
        response = await client.get("/api/v1/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_sites"] == 0
        assert data["published_sites"] == 0
        assert data["draft_sites"] == 0
        assert data["total_categories"] == 0
        assert data["total_news"] == 0
        assert data["published_news"] == 0
        assert data["total_timeline_events"] == 0
        assert data["published_timeline_events"] == 0
        assert data["total_visit_info"] == 0
        assert data["active_visit_info"] == 0

    @pytest.mark.asyncio
    async def test_get_stats_with_data(self, client: AsyncClient, db_session):
        """Test getting stats with data in database."""
        # Create a category
        category = HeritageCategory(
            name="Test Category",
            name_zh="測試類別",
        )
        db_session.add(category)

        # Create heritage sites
        site1 = HeritageSite(
            name="Published Site",
            name_zh="已發布景點",
            slug="published-site",
            city="Taipei",
            is_published=True,
        )
        site2 = HeritageSite(
            name="Draft Site",
            name_zh="草稿景點",
            slug="draft-site",
            city="Taipei",
            is_published=False,
        )
        db_session.add_all([site1, site2])

        # Create news
        news1 = News(
            title="Published News",
            title_zh="已發布新聞",
            slug="published-news",
            is_published=True,
        )
        news2 = News(
            title="Draft News",
            title_zh="草稿新聞",
            slug="draft-news",
            is_published=False,
        )
        db_session.add_all([news1, news2])

        # Create timeline events
        event1 = TimelineEvent(
            year=1900,
            title="Published Event",
            title_zh="已發布事件",
            is_published=True,
        )
        event2 = TimelineEvent(
            year=1901,
            title="Draft Event",
            title_zh="草稿事件",
            is_published=False,
        )
        db_session.add_all([event1, event2])

        # Create visit info
        info1 = VisitInfo(
            section="active",
            title="Active Info",
            title_zh="活躍資訊",
            is_active=True,
        )
        info2 = VisitInfo(
            section="inactive",
            title="Inactive Info",
            title_zh="非活躍資訊",
            is_active=False,
        )
        db_session.add_all([info1, info2])

        await db_session.flush()

        response = await client.get("/api/v1/dashboard/stats")
        assert response.status_code == 200
        data = response.json()

        assert data["total_sites"] == 2
        assert data["published_sites"] == 1
        assert data["draft_sites"] == 1
        assert data["total_categories"] == 1
        assert data["total_news"] == 2
        assert data["published_news"] == 1
        assert data["total_timeline_events"] == 2
        assert data["published_timeline_events"] == 1
        assert data["total_visit_info"] == 2
        assert data["active_visit_info"] == 1
