"""Tests for timeline API endpoints."""

import pytest
from httpx import AsyncClient

from app.models.timeline import TimelineEvent


@pytest.fixture
async def timeline_event(db_session):
    """Create a test timeline event."""
    event = TimelineEvent(
        year=1895,
        month=5,
        day=15,
        era="Meiji",
        era_year="28",
        title="Historic Event",
        title_zh="歷史事件",
        description="A significant event",
        description_zh="重要事件",
        category="construction",
        importance="high",
        is_published=True,
    )
    db_session.add(event)
    await db_session.flush()
    await db_session.refresh(event)
    return event


@pytest.fixture
async def unpublished_event(db_session):
    """Create an unpublished timeline event."""
    event = TimelineEvent(
        year=1900,
        title="Unpublished Event",
        title_zh="未發布事件",
        is_published=False,
    )
    db_session.add(event)
    await db_session.flush()
    await db_session.refresh(event)
    return event


class TestListTimelineEvents:
    """Tests for list timeline events endpoint."""

    @pytest.mark.asyncio
    async def test_list_events_empty(self, client: AsyncClient):
        """Test listing events when empty."""
        response = await client.get("/api/v1/timeline")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_events_with_items(self, client: AsyncClient, timeline_event):
        """Test listing events with items."""
        response = await client.get("/api/v1/timeline")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Historic Event"
        assert data[0]["year"] == 1895

    @pytest.mark.asyncio
    async def test_list_events_excludes_unpublished(
        self, client: AsyncClient, timeline_event, unpublished_event
    ):
        """Test that unpublished events are excluded by default."""
        response = await client.get("/api/v1/timeline")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Historic Event"

    @pytest.mark.asyncio
    async def test_list_events_include_unpublished(
        self, client: AsyncClient, timeline_event, unpublished_event
    ):
        """Test listing all events including unpublished."""
        response = await client.get("/api/v1/timeline?published_only=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_list_events_filter_by_category(self, client: AsyncClient, db_session):
        """Test filtering events by category."""
        event1 = TimelineEvent(
            year=1880,
            title="Event 1",
            title_zh="事件1",
            category="construction",
            is_published=True,
        )
        event2 = TimelineEvent(
            year=1890,
            title="Event 2",
            title_zh="事件2",
            category="renovation",
            is_published=True,
        )
        db_session.add_all([event1, event2])
        await db_session.flush()

        response = await client.get("/api/v1/timeline?category=construction")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"] == "construction"

    @pytest.mark.asyncio
    async def test_list_events_ordered_by_year(self, client: AsyncClient, db_session):
        """Test that events are ordered by year ascending."""
        event1 = TimelineEvent(
            year=1920,
            title="Later Event",
            title_zh="後來事件",
            is_published=True,
        )
        event2 = TimelineEvent(
            year=1880,
            title="Earlier Event",
            title_zh="早期事件",
            is_published=True,
        )
        db_session.add_all([event1, event2])
        await db_session.flush()

        response = await client.get("/api/v1/timeline")
        assert response.status_code == 200
        data = response.json()
        assert data[0]["year"] == 1880
        assert data[1]["year"] == 1920


class TestGetTimelineEvent:
    """Tests for get timeline event by ID endpoint."""

    @pytest.mark.asyncio
    async def test_get_event_by_id(self, client: AsyncClient, timeline_event):
        """Test getting event by ID."""
        response = await client.get(f"/api/v1/timeline/{timeline_event.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Historic Event"
        assert data["year"] == 1895
        assert data["era"] == "Meiji"

    @pytest.mark.asyncio
    async def test_get_event_not_found(self, client: AsyncClient):
        """Test getting non-existent event."""
        response = await client.get("/api/v1/timeline/9999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCreateTimelineEvent:
    """Tests for create timeline event endpoint."""

    @pytest.mark.asyncio
    async def test_create_event(self, client: AsyncClient):
        """Test creating a timeline event."""
        event_data = {
            "year": 1910,
            "month": 3,
            "title": "New Event",
            "title_zh": "新事件",
            "description": "A new historic event",
            "is_published": True,
        }
        response = await client.post("/api/v1/timeline", json=event_data)
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "New Event"
        assert data["year"] == 1910
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_event_minimal(self, client: AsyncClient):
        """Test creating event with minimal required fields."""
        event_data = {
            "year": 1900,
            "title": "Minimal Event",
            "title_zh": "最小事件",
        }
        response = await client.post("/api/v1/timeline", json=event_data)
        assert response.status_code == 201

    @pytest.mark.asyncio
    async def test_create_event_with_era(self, client: AsyncClient):
        """Test creating event with era information."""
        event_data = {
            "year": 1912,
            "era": "Taisho",
            "era_year": "1",
            "title": "Taisho Event",
            "title_zh": "大正事件",
        }
        response = await client.post("/api/v1/timeline", json=event_data)
        assert response.status_code == 201
        data = response.json()
        assert data["era"] == "Taisho"
        assert data["era_year"] == "1"


class TestUpdateTimelineEvent:
    """Tests for update timeline event endpoint."""

    @pytest.mark.asyncio
    async def test_update_event(self, client: AsyncClient, timeline_event):
        """Test updating a timeline event."""
        update_data = {"title": "Updated Event"}
        response = await client.patch(
            f"/api/v1/timeline/{timeline_event.id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Event"
        # Original fields should be preserved
        assert data["year"] == 1895

    @pytest.mark.asyncio
    async def test_update_event_not_found(self, client: AsyncClient):
        """Test updating non-existent event."""
        update_data = {"title": "Updated Event"}
        response = await client.patch("/api/v1/timeline/9999", json=update_data)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_event_multiple_fields(
        self, client: AsyncClient, timeline_event
    ):
        """Test updating multiple fields."""
        update_data = {
            "year": 1896,
            "title": "New Title",
            "importance": "normal",
        }
        response = await client.patch(
            f"/api/v1/timeline/{timeline_event.id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["year"] == 1896
        assert data["title"] == "New Title"
        assert data["importance"] == "normal"


class TestDeleteTimelineEvent:
    """Tests for delete timeline event endpoint."""

    @pytest.mark.asyncio
    async def test_delete_event(self, client: AsyncClient, timeline_event):
        """Test deleting a timeline event."""
        event_id = timeline_event.id
        response = await client.delete(f"/api/v1/timeline/{event_id}")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_delete_event_not_found(self, client: AsyncClient):
        """Test deleting non-existent event."""
        response = await client.delete("/api/v1/timeline/9999")
        assert response.status_code == 404
