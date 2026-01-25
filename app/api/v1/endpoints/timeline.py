"""Timeline API endpoints."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession
from app.models.timeline import TimelineEvent
from app.schemas.timeline import (
    TimelineEventCreate,
    TimelineEventResponse,
    TimelineEventUpdate,
)

router = APIRouter()


@router.get("", response_model=list[TimelineEventResponse])
async def list_timeline_events(
    db: DbSession,
    skip: int = 0,
    limit: int = 100,
    category: str | None = None,
    published_only: bool = True,
):
    """List timeline events with optional filtering."""
    query = select(TimelineEvent)

    if published_only:
        query = query.where(TimelineEvent.is_published == True)  # noqa: E712
    if category:
        query = query.where(TimelineEvent.category == category)

    query = query.order_by(TimelineEvent.year.asc()).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{event_id}", response_model=TimelineEventResponse)
async def get_timeline_event(db: DbSession, event_id: int):
    """Get timeline event by ID."""
    query = select(TimelineEvent).where(TimelineEvent.id == event_id)
    result = await db.execute(query)
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timeline event not found",
        )
    return event


@router.post("", response_model=TimelineEventResponse, status_code=status.HTTP_201_CREATED)
async def create_timeline_event(db: DbSession, event_in: TimelineEventCreate):
    """Create a new timeline event."""
    event = TimelineEvent(**event_in.model_dump())
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


@router.patch("/{event_id}", response_model=TimelineEventResponse)
async def update_timeline_event(
    db: DbSession,
    event_id: int,
    event_in: TimelineEventUpdate,
):
    """Update a timeline event."""
    query = select(TimelineEvent).where(TimelineEvent.id == event_id)
    result = await db.execute(query)
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timeline event not found",
        )

    update_data = event_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(event, field, value)

    await db.flush()
    await db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_timeline_event(db: DbSession, event_id: int):
    """Delete a timeline event."""
    query = select(TimelineEvent).where(TimelineEvent.id == event_id)
    result = await db.execute(query)
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Timeline event not found",
        )
    await db.delete(event)
