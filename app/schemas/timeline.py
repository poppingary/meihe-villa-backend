"""Pydantic schemas for timeline events."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TimelineEventBase(BaseModel):
    """Base schema for timeline event."""

    year: int
    month: int | None = None
    day: int | None = None
    era: str | None = None
    era_year: str | None = None
    title: str
    title_zh: str
    description: str | None = None
    description_zh: str | None = None
    image: str | None = None
    category: str | None = None
    importance: str = "normal"
    is_published: bool = True


class TimelineEventCreate(TimelineEventBase):
    """Schema for creating timeline event."""

    pass


class TimelineEventUpdate(BaseModel):
    """Schema for updating timeline event (all fields optional)."""

    year: int | None = None
    month: int | None = None
    day: int | None = None
    era: str | None = None
    era_year: str | None = None
    title: str | None = None
    title_zh: str | None = None
    description: str | None = None
    description_zh: str | None = None
    image: str | None = None
    category: str | None = None
    importance: str | None = None
    is_published: bool | None = None


class TimelineEventResponse(TimelineEventBase):
    """Schema for timeline event response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
