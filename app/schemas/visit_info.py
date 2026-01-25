"""Pydantic schemas for visit information."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class VisitInfoBase(BaseModel):
    """Base schema for visit info."""

    section: str
    title: str
    title_zh: str
    content: str | None = None
    content_zh: str | None = None
    extra_data: str | None = None
    display_order: int = 0
    is_active: bool = True


class VisitInfoCreate(VisitInfoBase):
    """Schema for creating visit info."""

    pass


class VisitInfoUpdate(BaseModel):
    """Schema for updating visit info (all fields optional)."""

    section: str | None = None
    title: str | None = None
    title_zh: str | None = None
    content: str | None = None
    content_zh: str | None = None
    extra_data: str | None = None
    display_order: int | None = None
    is_active: bool | None = None


class VisitInfoResponse(VisitInfoBase):
    """Schema for visit info response."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
