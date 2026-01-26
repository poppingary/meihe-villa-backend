"""Pydantic schemas for news/announcements."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class NewsBase(BaseModel):
    """Base schema for news."""

    title: str
    title_zh: str
    slug: str
    summary: str | None = None
    summary_zh: str | None = None
    content: str | None = None
    content_zh: str | None = None
    featured_image: str | None = None
    images: str | None = None  # JSON array of image URLs
    category: str | None = None
    is_published: bool = False
    published_at: datetime | None = None


class NewsCreate(NewsBase):
    """Schema for creating news."""

    pass


class NewsUpdate(BaseModel):
    """Schema for updating news (all fields optional)."""

    title: str | None = None
    title_zh: str | None = None
    slug: str | None = None
    summary: str | None = None
    summary_zh: str | None = None
    content: str | None = None
    content_zh: str | None = None
    featured_image: str | None = None
    images: str | None = None
    category: str | None = None
    is_published: bool | None = None
    published_at: datetime | None = None


class NewsResponse(NewsBase):
    """Schema for news response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
